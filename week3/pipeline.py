"""Reproducible, offline Week 3 baseline; NumPy and Python standard library only."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                    allow_nan=False), encoding='utf-8')


def label(obj):
    return obj.get('name') if isinstance(obj, dict) else None


def geometry(x, y):
    if not (math.isfinite(x) and math.isfinite(y) and 0 <= x <= 120 and 0 <= y <= 80):
        raise ValueError('Invalid StatsBomb coordinates')
    if x == 120 and y in (36, 44):
        raise ValueError('Shot at a goalpost has an undefined viewing angle')
    dx = 120 - x
    return math.hypot(dx, y - 40), math.atan2(8 * dx, dx * dx + (y - 40)**2 - 16)


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -40, 40)))


def metrics(y, p):
    p = np.asarray(p)
    c = np.clip(p, 1e-12, 1 - 1e-12)
    positive, negative = p[y == 1], p[y == 0]
    # Pairwise definition also handles probability ties correctly.
    auc = float(np.mean([(np.sum(a > negative) + .5 * np.sum(a == negative)) /
                         len(negative) for a in positive])) if len(positive) and len(negative) else None
    bins = []
    for k in range(10):
        mask = (p >= k / 10) & (p < (k + 1) / 10 if k < 9 else p <= 1)
        if mask.any():
            bins.append(dict(lower=k / 10, upper=(k + 1) / 10,
                             shots=int(mask.sum()), mean_xg=float(p[mask].mean()),
                             goal_rate=float(y[mask].mean())))
    return dict(shots=len(y), goals=int(y.sum()), goal_rate=float(y.mean()),
                mean_xg=float(p.mean()), log_loss=float(-(y * np.log(c) + (1-y) * np.log(1-c)).mean()),
                brier_score=float(np.mean((p-y)**2)), roc_auc=auc, calibration_bins=bins)


def fit(features, target):
    mean, scale = features.mean(axis=0), features.std(axis=0)
    scale[scale == 0] = 1
    x = np.column_stack([np.ones(len(features)), (features-mean)/scale])
    rate = float(target.mean())
    if not 0 < rate < 1:
        raise ValueError('Training set must contain both goals and non-goals')
    beta = np.array([math.log(rate/(1-rate)), 0., 0.])
    penalty = np.diag([0., 1., 1.])

    def objective(b):
        z = x @ b
        return float(np.sum(np.logaddexp(0, z)-target*z) + .5*b@penalty@b)

    for iteration in range(100):
        p = sigmoid(x@beta)
        gradient = x.T@(p-target)+penalty@beta
        hessian = x.T@((p*(1-p))[:, None]*x)+penalty
        step = np.linalg.solve(hessian, gradient)
        factor = 1.
        while objective(beta-factor*step) > objective(beta) and factor > 1e-8:
            factor /= 2
        if objective(beta-factor*step) > objective(beta):
            raise RuntimeError('Optimizer line search failed')
        beta -= factor*step
        if np.max(np.abs(factor*step)) < 1e-8:
            return dict(mean=mean.tolist(), scale=scale.tolist(), beta=beta.tolist(),
                        train_goal_rate=rate, iterations=iteration+1, converged=True,
                        features=['distance_sb_units', 'angle_rad'], l2_penalty=1.,
                        intercept_penalized=False)
    raise RuntimeError('Baseline did not converge')


def predict(model, features):
    x = np.column_stack([np.ones(len(features)),
                         (features-np.array(model['mean']))/np.array(model['scale'])])
    return sigmoid(x@np.array(model['beta']))


def run(matches_path, raw_path, output):
    output.mkdir(parents=True, exist_ok=True)
    matches = sorted(read(matches_path), key=lambda m: (m['match_date'], m['match_id']))
    if len(matches) < 5 or len({m['match_id'] for m in matches}) != len(matches):
        raise ValueError('Need at least five distinct matches')
    # Current verified execution uses the Week 2 EPL manifest, within the agreed scope.
    # An expanded manifest must be curated to European competitions or FIFA World Cup.
    european_countries = {'England', 'Spain', 'Germany', 'Italy', 'France', 'Portugal',
                          'Netherlands', 'Belgium', 'Scotland', 'Wales', 'Northern Ireland',
                          'Republic of Ireland', 'Austria', 'Switzerland', 'Denmark', 'Sweden',
                          'Norway', 'Finland', 'Greece', 'Poland', 'Croatia', 'Serbia',
                          'Turkey', 'Russia', 'Ukraine', 'Czech Republic', 'Romania'}
    for m in matches:
        comp = m['competition']
        european = comp.get('country_name') in european_countries or comp['competition_name'].startswith('UEFA ')
        if not (european or comp['competition_name'] == 'FIFA World Cup'):
            raise ValueError(f"Outside supported scope: {comp}")
        if m['match_date'] <= '2000-12-31' or any(m[t].get(f'{t}_gender') != 'male' for t in ['home_team', 'away_team']):
            raise ValueError('Only men, match dates from 2001 onward')
    rows, seen, manifest, counts = [], set(), [], Counter()
    reference_hashes = {r['match_id']: r['sha256'] for r in read(ROOT/'source_manifest.json')}
    for m in matches:
        mid = m['match_id']
        payload = (raw_path / f'events_{mid}.json').read_bytes()
        if mid in reference_hashes and hashlib.sha256(payload).hexdigest() != reference_hashes[mid]:
            raise ValueError(f'Source checksum mismatch for match {mid}')
        manifest.append(dict(match_id=mid, sha256=hashlib.sha256(payload).hexdigest()))
        for e in json.loads(payload):
            counts['all_events'] += 1
            if label(e.get('type')) != 'Shot':
                continue
            counts['all_shots'] += 1
            eid = e.get('id')
            if not eid:
                counts['missing_id'] += 1
                continue
            if eid in seen:
                # Conflicting duplicates cannot safely be resolved by keeping the first.
                raise ValueError(f'Duplicate Shot ID: {eid}')
            seen.add(eid)
            shot = e.get('shot', {})
            reason = None
            if e.get('period') not in [1, 2, 3, 4]:
                reason = 'excluded_period'
            elif label(shot.get('type')) == 'Penalty':
                reason = 'excluded_penalty'
            elif not label(shot.get('type')) or not label(shot.get('outcome')):
                reason = 'missing_type_or_outcome'
            loc = e.get('location')
            valid = isinstance(loc, list) and len(loc) >= 2 and all(
                isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v) for v in loc[:2])
            valid = valid and 0 <= loc[0] <= 120 and 0 <= loc[1] <= 80
            if reason is None and not valid:
                reason = 'invalid_location'
            if reason is None and loc[0] == 120 and loc[1] in (36, 44):
                reason = 'undefined_goalpost_angle'
            if reason:
                counts[reason] += 1
                continue
            distance, angle = geometry(*loc[:2])
            rows.append(dict(event_id=eid, match_id=mid, match_date=m['match_date'],
                             x=loc[0], y=loc[1], distance_sb_units=distance, angle_rad=angle,
                             goal=int(label(shot['outcome']) == 'Goal')))
    cut1, cut2 = int(len(matches)*.6), int(len(matches)*.8)
    split = dict(train=matches[:cut1], validation=matches[cut1:cut2], test=matches[cut2:])
    membership = {m['match_id']: s for s, ms in split.items() for m in ms}
    for row in rows:
        row['split'] = membership[row['match_id']]
    sets = {s: [r for r in rows if r['split'] == s] for s in split}
    if not all(sets.values()):
        raise ValueError('Each split needs eligible shots')
    features = {s: np.array([[r['distance_sb_units'], r['angle_rad']] for r in rs]) for s, rs in sets.items()}
    targets = {s: np.array([r['goal'] for r in rs], dtype=float) for s, rs in sets.items()}
    model = fit(features['train'], targets['train'])
    evaluation = {}
    for s, rs in sets.items():
        probabilities = predict(model, features[s])
        evaluation[s] = dict(constant=metrics(targets[s], np.full(len(rs), model['train_goal_rate'])),
                             logistic=metrics(targets[s], probabilities))
        for row, p in zip(rs, probabilities):
            row.update(xg=float(p), constant_probability=model['train_goal_rate'])
    with (output/'predictions.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    save(output/'model.json', model)
    save(output/'metrics.json', evaluation)
    save(output/'split_matches.json', {s: [m['match_id'] for m in ms] for s, ms in split.items()})
    save(output/'data_audit.json', dict(counts=counts, retained_shots=len(rows),
         goals=sum(r['goal'] for r in rows), selected_matches=len(matches),
         first_date=matches[0]['match_date'], last_date=matches[-1]['match_date'],
         competitions=sorted({m['competition']['competition_name'] for m in matches}),
         exclusion_policy='First applicable reason; duplicate Shot IDs fail the run',
         source_snapshot=read(ROOT/'snapshot.json') if matches_path.resolve() == (ROOT/'selected_matches.json').resolve() else None,
         provenance_note='Known pilot event hashes verified; expanded sources need their own pinned manifest.',
         source_manifest=manifest,
         match_manifest_sha256=hashlib.sha256(matches_path.read_bytes()).hexdigest(),
         python=platform.python_version(), numpy=np.__version__))
    print(json.dumps(evaluation['test'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matches', type=Path, default=ROOT/'selected_matches.json')
    parser.add_argument('--raw', type=Path, default=ROOT/'raw')
    parser.add_argument('--output', type=Path, default=ROOT/'week3/results')
    args = parser.parse_args()
    run(args.matches, args.raw, args.output)
