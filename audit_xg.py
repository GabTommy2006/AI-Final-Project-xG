"""Offline audit + xG baseline for download.ps1 cache; Python3 + numpy only."""
import csv
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def dump(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')

def name(obj):
    return obj.get('name') if isinstance(obj, dict) else None

def write_csv(filename, rows):
    with (ROOT / filename).open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -40, 40)))

def evaluate(y, p):
    c = np.clip(p, 1e-12, 1-1e-12)
    pos = int(y.sum())
    neg = len(y)-pos
    order = np.argsort(p, kind='mergesort')
    rank = np.empty(len(p))
    i = 0
    while i < len(p):
        j = i+1
        while j < len(p) and p[order[j]] == p[order[i]]:
            j += 1
        rank[order[i:j]] = (i+1+j)/2
        i = j
    auc = float((rank[y == 1].sum()-pos*(pos+1)/2)/(pos*neg)) if pos and neg else None
    bins = []
    for k in range(10):
        lo, hi = k/10, (k+1)/10
        mask = (p >= lo) & ((p < hi) if k < 9 else (p <= hi))
        if mask.any():
            bins.append({'lower':lo,'upper':hi,'shots':int(mask.sum()),'mean_probability':float(p[mask].mean()),'goal_rate':float(y[mask].mean())})
    return {'shots':len(y),'goals':pos,'goal_rate':float(y.mean()),'mean_prediction':float(p.mean()),
            'log_loss':float(-(y*np.log(c)+(1-y)*np.log(1-c)).mean()),
            'brier_score':float(((p-y)**2).mean()),'roc_auc':auc,'calibration_bins':bins}

# STEP 1: Read the pinned source version and chronological match selection.
snapshot = load(ROOT / 'snapshot.json')
matches = sorted(load(ROOT / 'selected_matches.json'), key=lambda m:(m['match_date'],m['match_id']))
all_matches = load(RAW / 'matches_2_27.json')
# STEP 2: Extract Shot events; create features/labels and preserve optional-field presence.
rows, manifest, all_ids = [], [], Counter()
missing_event_ids = 0
for m in matches:
    mid = m['match_id']
    p = RAW / f'events_{mid}.json'
    payload = p.read_bytes()
    events = json.loads(payload)
    manifest.append({'match_id':mid,'match_date':m['match_date'],'events':len(events),
                     'sha256':hashlib.sha256(payload).hexdigest(),
                     'url':f"https://raw.githubusercontent.com/hudl/open-data/{snapshot['git_commit']}/data/events/{mid}.json"})
    for e in events:
        if e.get('id') is None:
            missing_event_ids += 1
        else:
            all_ids[e['id']] += 1
        if name(e.get('type')) != 'Shot':
            continue
        s = e.get('shot',{})
        loc = e.get('location')
        valid = (isinstance(loc,list) and len(loc)>=2 and all(isinstance(x,(int,float)) and math.isfinite(x) for x in loc[:2]) and 0<=loc[0]<=120 and 0<=loc[1]<=80)
        x,y = loc[:2] if valid else (None,None)
        dx = 120-x if valid else None
        distance = math.hypot(dx,y-40) if valid else None
        angle = math.atan2(abs(8*dx),dx*dx+(y-40)**2-16) if valid else None
        outcome = name(s.get('outcome'))
        rows.append({'event_id':e.get('id'),'match_id':mid,'match_date':m['match_date'],'period':e.get('period'),
                     'minute':e.get('minute'),'team':name(e.get('team')),'player':name(e.get('player')),
                     'x':x,'y':y,'distance_sb_units':distance,'angle_rad':angle,
                     'body_part':name(s.get('body_part')),'shot_type':name(s.get('type')),
                     'play_pattern':name(e.get('play_pattern')),'technique':name(s.get('technique')),
                     'outcome':outcome,'goal':int(outcome=='Goal') if outcome else None,
                     'under_pressure_raw':e.get('under_pressure'),'under_pressure_present':'under_pressure' in e,
                     'first_time_raw':s.get('first_time'),'first_time_present':'first_time' in s,
                     'freeze_frame_present':isinstance(s.get('freeze_frame'),list),
                     'provider_xg_reference_only':s.get('statsbomb_xg'),'location_valid':valid})

# STEP 3: Audit missing fields, duplicate IDs and optional qualifiers.
n = len(rows)
shot_ids = Counter(r['event_id'] for r in rows if r['event_id'] is not None)
missing = {}
for field in ['event_id','x','y','body_part','shot_type','play_pattern','technique','outcome','player','team','provider_xg_reference_only']:
    absent = sum(r[field] is None for r in rows)
    missing[field] = {'missing':absent,'denominator_all_shots':n,'percent':100*absent/n}
optional = {}
for raw,present in [('under_pressure_raw','under_pressure_present'),('first_time_raw','first_time_present')]:
    optional[raw] = {'absent':sum(not r[present] for r in rows),'explicit_true':sum(r[raw] is True for r in rows),
                     'explicit_false':sum(r[raw] is False for r in rows),'explicit_null':sum(r[present] and r[raw] is None for r in rows),
                     'denominator_all_shots':n,
                     'interpretation':'Optional qualifier; absence differs from an observed explicit false. Preserve presence flag; not used as model feature.'}

# STEP 4: Keep valid non-penalty shots in regulation/extra-time periods.
eligible = [r for r in rows if r['period'] in (1,2,3,4) and r['shot_type'] is not None and r['shot_type']!='Penalty' and r['location_valid'] and r['goal'] is not None]
audit = {'status':'ACTUAL_COMPUTED_AUDIT','snapshot':snapshot,'python_version':platform.python_version(),
         'available_matches':len(all_matches),'selected_matches':len(matches),'all_matches_included':len(matches)==len(all_matches),
         'first_match_date':matches[0]['match_date'],'last_match_date':matches[-1]['match_date'],
         'all_events':sum(m['events'] for m in manifest),'all_shots':n,'goals_all_shots':sum(r['goal']==1 for r in rows),
         'goal_rate_all_shots':sum(r['goal']==1 for r in rows)/n,'nonpenalty_eligible_shots':len(eligible),
         'nonpenalty_eligible_goals':sum(r['goal']==1 for r in eligible),
         'shot_types':dict(Counter(r['shot_type'] for r in rows)),'body_parts':dict(Counter(r['body_part'] for r in rows)),
         'periods':dict(Counter(r['period'] for r in rows)),'outcomes':dict(Counter(r['outcome'] for r in rows)),
         'duplicates':{'all_event_duplicate_id_values':sum(c>1 for c in all_ids.values()),'all_event_excess_duplicate_rows':sum(c-1 for c in all_ids.values()),
                       'shot_duplicate_id_values':sum(c>1 for c in shot_ids.values()),'shot_excess_duplicate_rows':sum(c-1 for c in shot_ids.values()),'all_event_missing_ids':missing_event_ids},
         'missing':missing,'optional_boolean_qualifiers':optional,'invalid_locations':sum(not r['location_valid'] for r in rows),
         'freeze_frame_present_count':sum(r['freeze_frame_present'] for r in rows),
         'filter':'Only type=Shot. Baseline excludes Penalty, period outside1-4, invalid location, missing outcome or shot_type. Own Goal events are not Shot events.',
         'bias_risks':['One historic English elite mens league season; do not infer transfer to womens, youth or Vietnamese football.',
                       'If pilot subset, earliest matches only is not representative of a full season; label as pilot.',
                       'Only actions where a shot was taken; not a model of all attacking situations.',
                       'Goal minority class; probability metrics and calibration required.',
                       'Provider definitions and limited visible-player freeze frames affect measurement.']}
# STEP 5: Descriptive group summaries; these are not model predictions.
groups = {}
for field in ['body_part','shot_type','play_pattern']:
    groups[field] = []
    for value in sorted({r[field] for r in eligible}, key=str):
        subset = [r for r in eligible if r[field] == value]
        groups[field].append({'name':value,'shots':len(subset),'goals':sum(r['goal'] for r in subset),'goal_rate':sum(r['goal'] for r in subset)/len(subset)})
groups['distance_bands_sb_units'] = []
for lo,hi,label in [(0,10,'0-<10'),(10,20,'10-<20'),(20,30,'20-<30'),(30,float('inf'),'30+')]:
    subset = [r for r in eligible if lo<=r['distance_sb_units']<hi]
    if subset:
        groups['distance_bands_sb_units'].append({'name':label,'shots':len(subset),'goals':sum(r['goal'] for r in subset),'goal_rate':sum(r['goal'] for r in subset)/len(subset)})
dump('group_summaries.json',{'denominator':'Eligible nonpenalty Shot events periods1-4 with valid location and outcome; pooled pilot, descriptive only','eligible_shots':len(eligible),'groups':groups})
dump('audit.json',audit)
dump('source_manifest.json',manifest)
write_csv('shots.csv',rows)

# STEP 6: Split whole matches chronologically; no match crosses sets.
cut1,cut2 = int(len(matches)*.6),int(len(matches)*.8)
sm = {'train':matches[:cut1],'validation':matches[cut1:cut2],'test':matches[cut2:]}
sids = {k:{m['match_id'] for m in v} for k,v in sm.items()}
sr = {k:[r for r in eligible if r['match_id'] in ids] for k,ids in sids.items()}
assert all(sr.values()), 'Need more matches for split'
assert not(sids['train'] & sids['validation'] or sids['train'] & sids['test'] or sids['validation'] & sids['test'])
xr = {k:np.array([[r['distance_sb_units'],r['angle_rad']] for r in v],dtype=float) for k,v in sr.items()}
y = {k:np.array([r['goal'] for r in v],dtype=float) for k,v in sr.items()}
# STEP 7: Fit scaling on TRAIN only; add an intercept column.
mean,std = xr['train'].mean(axis=0),xr['train'].std(axis=0)
std[std==0]=1
X = {k:np.column_stack([np.ones(len(v)),(v-mean)/std]) for k,v in xr.items()}
rate = float(y['train'].mean())
beta = np.array([math.log(rate/(1-rate)),0.,0.])
penalty = np.diag([0.,1.,1.])
# STEP 8: Regularized binary negative log-likelihood; fixed penalty, no tuning.
def loss(b):
    z = X['train']@b
    return float((np.logaddexp(0,z)-y['train']*z).sum()+.5*b@penalty@b)
# STEP 9: Newton optimization with backtracking on the training objective.
converged = False
for iteration in range(100):
    p = sigmoid(X['train']@beta)
    grad = X['train'].T@(p-y['train'])+penalty@beta
    hessian = X['train'].T@((p*(1-p))[:,None]*X['train'])+penalty
    step = np.linalg.solve(hessian,grad)
    scale,before = 1.,loss(beta)
    while scale>1e-8 and loss(beta-scale*step)>before:
        scale/=2
    beta-=scale*step
    if float(np.max(np.abs(scale*step)))<1e-8:
        converged=True
        break
# STEP 10: Report constant and logistic probabilities on each fixed split.
predictions,evaluation = [],{}
for split,rs in sr.items():
    cp = np.repeat(rate,len(rs))
    lp = sigmoid(X[split]@beta)
    evaluation[split]={'constant_train_rate':evaluate(y[split],cp),'logistic_distance_angle':evaluate(y[split],lp)}
    for row,c,l in zip(rs,cp,lp):
        predictions.append({'event_id':row['event_id'],'match_id':row['match_id'],'split':split,'goal':row['goal'],'constant_probability':float(c),'logistic_xg':float(l)})
result = {'status':'ACTUAL_PRELIMINARY_BASELINE','features':['distance_sb_units','angle_rad'],
          'feature_geometry':'StatsBomb coordinate system120x80; goal center(120,40),posts(120,36),(120,44); not metric distance.',
          'split_policy':'Chronological(match_date,match_id),match-disjoint60/20/20; dates can coincide across boundaries.',
          'split_counts':{k:{'matches':len(v),'shots':len(sr[k]),'goals':int(y[k].sum()),'first_date':v[0]['match_date'],'last_date':v[-1]['match_date']} for k,v in sm.items()},
          'model':'Logistic regression, fixed L2 coefficient penalty1, unpenalized intercept; features standardized using train only.',
          'no_leakage':'No outcomes, provider xG, end_location, shot-on-target, future events or test-fitted preprocessing in inputs.',
          'optimization':{'method':'Newton with backtracking','converged':converged,'iterations':iteration+1},
          'numpy_version':np.__version__,'coefficients_intercept_distance_angle':beta.tolist(),
          'train_feature_mean':mean.tolist(),'train_feature_std_population':std.tolist(),
          'evaluation':evaluation,
          'limitations':['No hyperparameter search performed; fixed transparent baseline.',
                         'Single-season within-league evaluation; not prospective or cross-league validation.',
                         'Finite pilot sample is preliminary; no claim of statistical superiority.',
                         'Brier and log loss mix calibration and discrimination; inspect calibration bins as well.']}
# STEP 11: Save inspectable metrics, split IDs and per-shot predictions.
dump('model_metrics.json',result)
dump('split_matches.json',{k:[m['match_id'] for m in v] for k,v in sm.items()})
write_csv('predictions.csv',predictions)
print(json.dumps({'matches':len(matches),'shots':n,'nonpenalty_shots':len(eligible),'converged':converged,'test':evaluation['test']},ensure_ascii=False))
