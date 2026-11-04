import csv,json,math
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parent
a=json.loads((p/'audit.json').read_text()); m=json.loads((p/'model_metrics.json').read_text()); sp=json.loads((p/'split_matches.json').read_text())
rows=list(csv.DictReader((p/'shots.csv').open(encoding='utf-8-sig')))
pr=list(csv.DictReader((p/'predictions.csv').open(encoding='utf-8-sig')))
assert len(rows)==a['all_shots']==sum(a['outcomes'].values())==sum(a['body_parts'].values())==sum(a['shot_types'].values())
assert len(pr)==a['nonpenalty_eligible_shots']==sum(z['shots'] for z in m['split_counts'].values())
assert a['nonpenalty_eligible_goals']==sum(z['goals'] for z in m['split_counts'].values())
assert a['all_shots']-a['nonpenalty_eligible_shots']==a['shot_types']['Penalty']==19
for k in sp:
    for kk in sp:
        if k!=kk: assert not(set(sp[k]) & set(sp[kk]))
lookup={r['event_id']:r for r in rows}
train=[r for r in pr if r['split']=='train']
X0=np.array([[float(lookup[r['event_id']]['distance_sb_units']),float(lookup[r['event_id']]['angle_rad'])] for r in train])
y=np.array([int(r['goal']) for r in train])
b=np.array(m['coefficients_intercept_distance_angle']); avg=np.array(m['train_feature_mean']); std=np.array(m['train_feature_std_population']); X=np.column_stack([np.ones(len(y)),(X0-avg)/std]); prob=1/(1+np.exp(-(X@b)))
pen=np.diag([0.,1.,1.]); grad=X.T@(prob-y)+pen@b
assert np.max(np.abs(grad))<1e-7
assert np.max(np.abs(avg-X0.mean(axis=0)))<1e-12
# Geometry checked with vector-angle equivalent at all shots.
angle_diff=[]
for r in rows:
    x,y0=float(r['x']),float(r['y']); v1=np.array([120-x,36-y0]); v2=np.array([120-x,44-y0]); den=np.linalg.norm(v1)*np.linalg.norm(v2)
    if den:
        alt=math.acos(float(np.clip(v1@v2/den,-1,1))); angle_diff.append(abs(alt-float(r['angle_rad'])))
assert max(angle_diff)<1e-7
# Independent pairwise AUC, Brier and log loss for test.
test=[r for r in pr if r['split']=='test']; ty=np.array([int(r['goal']) for r in test]); tp=np.array([float(r['logistic_xg']) for r in test]); pp=tp[ty==1]; nn=tp[ty==0]; dif=pp[:,None]-nn[None,:]; auc=float(((dif>0)+.5*(dif==0)).mean())
assert abs(auc-m['evaluation']['test']['logistic_distance_angle']['roc_auc'])<1e-12
# Recalculate both proper losses independently from the saved test predictions.
for field, model_name in [('constant_probability','constant_train_rate'),('logistic_xg','logistic_distance_angle')]:
    test_p=np.array([float(r[field]) for r in test])
    clipped=np.clip(test_p,1e-12,1-1e-12)
    ll=float(-(ty*np.log(clipped)+(1-ty)*np.log(1-clipped)).mean())
    bs=float(((test_p-ty)**2).mean())
    assert abs(ll-m['evaluation']['test'][model_name]['log_loss'])<1e-12
    assert abs(bs-m['evaluation']['test'][model_name]['brier_score'])<1e-12

assert all(0<float(r['logistic_xg'])<1 for r in pr)
assert m['evaluation']['train']['logistic_distance_angle']['log_loss']<m['evaluation']['train']['constant_train_rate']['log_loss']
result={'checks':'passed','arithmetic_reconciliation':True,'match_disjoint_splits':True,'train_only_standardization':True,'objective_gradient_max_abs':float(np.max(np.abs(grad))),'geometry_vector_angle_max_difference_rad':max(angle_diff),'pairwise_test_auc':auc,'test_probability_range':[float(tp.min()),float(tp.max())],'penalty_shots':19,'penalty_goals':a['goals_all_shots']-a['nonpenalty_eligible_goals'],'warning':'Pilot only; test labels now inspected, so final untouched holdout must use different later matches.'}
(p/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))

