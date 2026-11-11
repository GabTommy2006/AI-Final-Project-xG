"""Shared, train-only preprocessing and probability evaluation for Week 4."""
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ['distance_sb_units', 'angle_rad']
CATEGORICAL = ['body_part', 'shot_type', 'play_pattern', 'technique']
MISSING = '__MISSING__'
SEED = 2026


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matrix(rows, context):
    result = []
    for row in rows:
        numeric = [float(row[f]) for f in NUMERIC]
        if not all(math.isfinite(v) for v in numeric):
            raise ValueError('Non-finite numeric feature')
        result.append(numeric + [(row.get(f) or MISSING) for f in CATEGORICAL] if context else numeric)
    return np.array(result, dtype=object if context else float)


def make_model(family, params):
    context = family.endswith('context')
    logistic = family.startswith('logistic')
    transformers = [('numeric', StandardScaler() if logistic else 'passthrough', [0, 1])]
    if context:
        transformers.append(('context', OneHotEncoder(handle_unknown='ignore', sparse_output=False), [2, 3, 4, 5]))
    prep = ColumnTransformer(transformers, remainder='drop')
    if logistic:
        model = LogisticRegression(C=params['C'], solver='lbfgs', penalty='l2',
                                   max_iter=2000, tol=1e-10, random_state=SEED)
    else:
        model = RandomForestClassifier(n_estimators=200, criterion='gini',
                    max_depth=params['max_depth'], min_samples_leaf=params['min_samples_leaf'],
                    max_features='sqrt', bootstrap=True, class_weight=None,
                    random_state=SEED, n_jobs=2)
    return Pipeline([('preprocess', prep), ('model', model)])


def score(y, probability):
    y, p = np.asarray(y, dtype=int), np.asarray(probability, dtype=float)
    if len(y) == 0 or len(y) != len(p) or not np.all(np.isfinite(p)) or np.any((p < 0) | (p > 1)):
        raise ValueError('Invalid probability vector')
    c = np.clip(p, 1e-12, 1-1e-12)  # Same reporting convention as Week 3.
    bins = []
    for k in range(10):
        mask = (p >= k/10) & ((p < (k+1)/10) if k < 9 else (p <= 1))
        if mask.any():
            bins.append(dict(lower=k/10, upper=(k+1)/10, shots=int(mask.sum()),
                mean_xg=float(p[mask].mean()), goal_rate=float(y[mask].mean())))
    return dict(shots=len(y), goals=int(y.sum()), goal_rate=float(y.mean()),
                mean_xg=float(p.mean()), log_loss=float(-np.mean(y*np.log(c)+(1-y)*np.log(1-c))),
                brier_score=float(brier_score_loss(y, p)),
                roc_auc=float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
                accuracy_at_0_5=float(accuracy_score(y, p >= .5)),
                f1_at_0_5=float(f1_score(y, p >= .5, zero_division=0)),
                calibration_bins=bins)


def frozen_probability(model, rows):
    x = np.array([[float(r[f]) for f in NUMERIC] for r in rows])
    z = (x-np.array(model['mean']))/np.array(model['scale'])
    # Preserve Week 3's operation order, including floating-point ties for ROC-AUC.
    design=np.column_stack([np.ones(len(x)),z])
    return 1/(1+np.exp(-np.clip(design@np.array(model['beta']), -40, 40)))


def load_dataset():
    source = ROOT/'week3/results/predictions.csv'
    with source.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    audit = read(ROOT/'week3/results/data_audit.json')
    split_ids = read(ROOT/'week3/results/split_matches.json')
    membership = {mid: split for split, mids in split_ids.items() for mid in mids}
    if len(membership) != sum(map(len, split_ids.values())):
        raise ValueError('A match crosses splits')
    seen = set()
    for r in rows:
        if r['event_id'] in seen:
            raise ValueError('Duplicate event ID')
        seen.add(r['event_id'])
        if r['split'] != membership.get(int(r['match_id'])):
            raise ValueError('Shot split differs from Week 3')
        if r['goal'] not in ['0', '1'] or r['shot_type'] == 'Penalty':
            raise ValueError('Invalid label or penalty')
        x, y = float(r['x']), float(r['y'])
        if not (0 <= x <= 120 and 0 <= y <= 80):
            raise ValueError('Invalid shot location')
        expected = [math.hypot(120-x, y-40), math.atan2(8*(120-x),(120-x)**2+(y-40)**2-16)]
        if not np.allclose(expected, [float(r[f]) for f in NUMERIC], atol=1e-12, rtol=1e-12):
            raise ValueError('Geometry mismatch')
    if len(rows) != audit['retained_shots'] or sum(int(r['goal']) for r in rows) != audit['goals']:
        raise ValueError('Dataset totals differ from Week 3')
    sets = {s: [r for r in rows if r['split'] == s] for s in ['train', 'validation', 'test']}
    expected = read(ROOT/'week3/results/split_summary.json')
    for s, rs in sets.items():
        if len(rs) != expected[s]['shots'] or len({r['match_id'] for r in rs}) != expected[s]['matches']:
            raise ValueError('Split counts differ from Week 3')
    baseline = read(ROOT/'week3/results/model.json')
    np.testing.assert_allclose(frozen_probability(baseline, rows), [float(r['xg']) for r in rows], atol=1e-12)
    return rows, sets


def choose_candidate(records):
    """Only validation fields are consulted; test data cannot influence this rule."""
    return min(records, key=lambda r:(r['validation']['log_loss'], r['validation']['brier_score'], r['id']))


def bundle_probability(bundle, rows):
    if bundle['kind'] == 'frozen_logistic':
        return frozen_probability(bundle['model'], rows)
    return bundle['model'].predict_proba(matrix(rows, bundle['context']))[:, 1]
