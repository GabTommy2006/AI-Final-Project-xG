"""Train controlled Week 4 comparisons; lock selection before test reporting."""
import argparse
import csv
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import time
import warnings

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning

from core import (ROOT, NUMERIC, CATEGORICAL, SEED, choose_candidate, frozen_probability,
                  load_dataset, make_model, matrix, read, save, score, sha)

OUT = ROOT/'week4/results'


def specifications():
    result = [dict(id=f'logistic_context_C{c:g}', family='logistic_context', params={'C':c}) for c in [.1, 1., 10.]]
    for family in ['forest_geometry', 'forest_context']:
        for depth in [6, 10, None]:
            for leaf in [20, 50]:
                result.append(dict(id=f'{family}_depth{depth}_leaf{leaf}', family=family,
                                   params=dict(max_depth=depth, min_samples_leaf=leaf)))
    return result


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    rows, sets = load_dataset()
    y = {s:np.array([int(r['goal']) for r in rs]) for s, rs in sets.items()}
    input_path = ROOT/'week3/results/predictions.csv'
    spec = specifications()
    plan = dict(created_utc=datetime.now(timezone.utc).isoformat(), seed=SEED,
        input_sha256=sha(input_path), week3_split_sha256=sha(ROOT/'week3/results/split_matches.json'),
        numeric_features=NUMERIC, categorical_features=CATEGORICAL, candidates=spec,
        selection='Lowest validation Log Loss; then Brier; then ID. Frozen Week 3 baseline may win.',
        test_policy='No candidate is scored on test until selection.json is written. Week 3 test already inspected.',
        fixed_forest_settings=dict(n_estimators=200, criterion='gini', bootstrap=True, max_features='sqrt', n_jobs=2),
        logistic_objective='scikit-learn L2 LogisticRegression, unpenalized intercept, C as inverse regularization; baseline parity checked',
        reporting_log_loss_clip=1e-12, class_weight=None, oversampling=False,
        python=platform.python_version(), versions={p:importlib.metadata.version(p) for p in ['numpy','scikit-learn','scipy','joblib','matplotlib','threadpoolctl']})
    save(OUT/'experiment_plan.json', plan)  # Written before any candidate fit/score.
    frozen = read(ROOT/'week3/results/model.json')
    baseline = dict(id='week3_logistic_geometry', family='baseline', params={},
        train=score(y['train'], frozen_probability(frozen, sets['train'])),
        validation=score(y['validation'], frozen_probability(frozen, sets['validation'])), fit_seconds=0.)
    models = {baseline['id']:dict(kind='frozen_logistic', model=frozen, context=False)}
    # Reproduce the existing objective with the library before attributing gains to context.
    refit = make_model('logistic_geometry', {'C':1.})
    with warnings.catch_warnings():
        warnings.simplefilter('error', ConvergenceWarning)
        refit.fit(matrix(sets['train'], False), y['train'])
    parity = float(np.max(np.abs(refit.predict_proba(matrix(sets['validation'], False))[:,1]-frozen_probability(frozen, sets['validation']))))
    if parity > 1e-5:
        raise RuntimeError(f'Library baseline parity failed: {parity}')
    save(OUT/'baseline_parity.json', dict(max_abs_validation_probability_difference=parity, tolerance=1e-5, passed=True))
    records = [baseline]
    for number, config in enumerate(spec, 1):
        context = config['family'].endswith('context')
        estimator = make_model(config['family'], config['params'])
        tick = time.perf_counter()
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            estimator.fit(matrix(sets['train'], context), y['train'])
        elapsed = time.perf_counter()-tick
        record = dict(**config, fit_seconds=elapsed,
            train=score(y['train'], estimator.predict_proba(matrix(sets['train'], context))[:,1]),
            validation=score(y['validation'], estimator.predict_proba(matrix(sets['validation'], context))[:,1]))
        records.append(record)
        models[config['id']] = dict(kind='sklearn', model=estimator, context=context)
        print(f"{number}/{len(spec)} {config['id']} validation LL={record['validation']['log_loss']:.6f}", flush=True)
    save(OUT/'validation_search.json', records)
    best = choose_candidate(records)
    family_winners = {f:choose_candidate([r for r in records if r['family']==f])['id'] for f in ['logistic_context','forest_geometry','forest_context']}
    selection = dict(selected_id=best['id'], params=best['params'], family=best['family'],
         selected_by='validation_log_loss', validation_log_loss=best['validation']['log_loss'],
         family_winners=family_winners, selected_utc=datetime.now(timezone.utc).isoformat(),
         test_used_for_selection=False, refit_on_train_plus_validation=False,
         baseline_input_sha256=plan['input_sha256'])
    save(OUT/'selection.json', selection)  # Selection is locked before test evaluation.
    selected = models[best['id']]
    selected.update(selected_id=best['id'], numeric_features=NUMERIC,
                    categorical_features=CATEGORICAL if selected['context'] else [],
                    input_sha256=plan['input_sha256'], params=best['params'])
    joblib.dump(selected, OUT/'selected_model.joblib', compress=3)

    report_ids = [baseline['id'], *family_winners.values()]
    matched = 'logistic_context_C1'
    if matched not in report_ids:
        report_ids.append(matched)  # Controls feature comparison at fixed regularization.
    evaluation, predictions = {}, []
    for s, rs in sets.items():
        by_model = {'constant_train_rate':np.full(len(rs), frozen['train_goal_rate'])}
        for mid in report_ids:
            bundle = models[mid]
            p = (frozen_probability(bundle['model'], rs) if bundle['kind']=='frozen_logistic' else
                 bundle['model'].predict_proba(matrix(rs,bundle['context']))[:,1])
            by_model[mid] = p
        evaluation[s] = {mid:score(y[s],p) for mid,p in by_model.items()}
        for i,row in enumerate(rs):
            predictions.append({**{key:row[key] for key in ['event_id','match_id','split','goal']},
                                **{mid:float(p[i]) for mid,p in by_model.items()}})
    save(OUT/'metrics.json', evaluation)
    with (OUT/'predictions.csv').open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(predictions[0]));writer.writeheader();writer.writerows(predictions)
    save(OUT/'preprocessing_audit.json', dict(
        train_feature_mean=refit.named_steps['preprocess'].named_transformers_['numeric'].mean_.tolist(),
        train_feature_scale=refit.named_steps['preprocess'].named_transformers_['numeric'].scale_.tolist(),
        categories={s:{f:dict(missing=sum(not r[f] for r in rs),values=sorted({r[f] or '__MISSING__' for r in rs})) for f in CATEGORICAL} for s,rs in sets.items()},
        fitted_context_categories={f:models[family_winners['logistic_context']]['model'].named_steps['preprocess'].named_transformers_['context'].categories_[i].tolist() for i,f in enumerate(CATEGORICAL)}))
    # Group errors for baseline and chosen model, on validation and reported test.
    errors = {}
    pred_by_id={r['event_id']:r for r in predictions}
    for s in ['validation','test']:
        rs=sets[s]; errors[s]={}
        for field in ['competition','body_part','shot_type','play_pattern','distance_band']:
            values={}
            for r in rs:
                distance=float(r['distance_sb_units'])
                value=('0-<10' if distance<10 else '10-<20' if distance<20 else '20-<30' if distance<30 else '30+') if field=='distance_band' else r[field] or '__MISSING__'
                values.setdefault(value,[]).append(r)
            errors[s][field]={}
            for value, group in sorted(values.items()):
                target=np.array([int(r['goal']) for r in group]); errors[s][field][value]={}
                for mid in [baseline['id'],best['id']]:
                    errors[s][field][value][mid]=score(target,np.array([pred_by_id[r['event_id']][mid] for r in group]))
                errors[s][field][value]['small_sample_warning']=len(group)<100 or int(target.sum())<10
    save(OUT/'error_analysis.json', errors)
    save(OUT/'runtime.json', dict(total_seconds=time.perf_counter()-started,
          completed_utc=datetime.now(timezone.utc).isoformat(), student_actual_hours=None))
    print(json.dumps(selection,indent=2))


if __name__=='__main__':
    run()
