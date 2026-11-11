"""Meaningful Week 4 checks: leakage boundaries, selection, serialization and metrics."""
import csv
import math
import unittest
import joblib
import numpy as np
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score
from core import (ROOT, NUMERIC, CATEGORICAL, choose_candidate, load_dataset, make_model,
                  matrix, read, score, sha, bundle_probability)
from predict import shot_row

OUT=ROOT/'week4/results'


class Week4Tests(unittest.TestCase):
    def test_known_metrics(self):
        result=score(np.array([0,1]),np.array([.2,.8]))
        self.assertAlmostEqual(result['log_loss'],-math.log(.8))
        self.assertAlmostEqual(result['brier_score'],.04)
        self.assertEqual(result['roc_auc'],1.)
        self.assertEqual(result['f1_at_0_5'],1.)
        self.assertEqual(score(np.array([0,1]),np.array([.5,.5]))['roc_auc'],.5)
        self.assertIsNone(score(np.array([0,0]),np.array([.1,.2]))['roc_auc'])

    def test_selection_ignores_test(self):
        records=[dict(id='a',validation=dict(log_loss=.2,brier_score=.1),test=dict(log_loss=100)),
                 dict(id='b',validation=dict(log_loss=.3,brier_score=.1),test=dict(log_loss=0))]
        self.assertEqual(choose_candidate(records)['id'],'a')
        records[0]['test']['log_loss']=0;records[1]['test']['log_loss']=100
        self.assertEqual(choose_candidate(records)['id'],'a')

    def test_train_only_preprocessing_and_unknown_categories(self):
        train=[dict(distance_sb_units=d,angle_rad=.1+d/100,body_part=b,shot_type='Open Play',
                    play_pattern='Regular Play',technique='Normal') for d,b in [(5,'Head'),(10,'Right Foot'),(15,'Head'),(20,'Right Foot')]]
        model=make_model('logistic_context',{'C':1.})
        model.fit(matrix(train,True),np.array([1,0,1,0]))
        prep=model.named_steps['preprocess']
        np.testing.assert_allclose(prep.named_transformers_['numeric'].mean_,[12.5,.225])
        before=[c.copy() for c in prep.named_transformers_['context'].categories_]
        row=dict(train[0],body_part='UNSEEN',technique=None,distance_sb_units=70)
        probability=model.predict_proba(matrix([row],True))[0,1]
        self.assertTrue(0<=probability<=1)
        for a,b in zip(before,prep.named_transformers_['context'].categories_):
            np.testing.assert_array_equal(a,b)
        np.testing.assert_allclose(prep.named_transformers_['numeric'].mean_,[12.5,.225])

    def test_inference_domain(self):
        for x,y in [(float('nan'),40),(-1,40),(120,36),(121,40)]:
            with self.assertRaises(ValueError): shot_row(x,y)
        with self.assertRaises(ValueError): shot_row(108,40,shot_type='Penalty')
        row=shot_row(108,40)
        self.assertEqual(row['distance_sb_units'],12)
        self.assertAlmostEqual(row['angle_rad'],2*math.atan(4/12))

    @classmethod
    def setUpClass(cls):
        cls.rows,cls.sets=load_dataset()

    def test_frozen_data_and_selection(self):
        plan=read(OUT/'experiment_plan.json');selection=read(OUT/'selection.json')
        self.assertEqual(plan['input_sha256'],sha(ROOT/'week3/results/predictions.csv'))
        self.assertEqual(plan['week3_split_sha256'],sha(ROOT/'week3/results/split_matches.json'))
        records=read(OUT/'validation_search.json')
        self.assertTrue(all('test' not in r for r in records))
        self.assertEqual(selection['selected_id'],choose_candidate(records)['id'])
        self.assertFalse(selection['test_used_for_selection'])
        self.assertFalse(selection['refit_on_train_plus_validation'])
        self.assertTrue(read(OUT/'baseline_parity.json')['passed'])
        bundle=joblib.load(OUT/'selected_model.joblib')
        self.assertEqual(bundle['input_sha256'],plan['input_sha256'])
        self.assertEqual(bundle['numeric_features'],NUMERIC)
        self.assertEqual(bundle['categorical_features'],CATEGORICAL if bundle['context'] else [])
        audit=read(OUT/'preprocessing_audit.json')
        for f,known in audit['fitted_context_categories'].items():
            self.assertEqual(set(known),{r[f] or '__MISSING__' for r in self.sets['train']})
        if bundle['kind']=='sklearn' and bundle['selected_id'].startswith('logistic'):
            scaler=bundle['model'].named_steps['preprocess'].named_transformers_['numeric']
            train=matrix(self.sets['train'],False)
            np.testing.assert_allclose(scaler.mean_,train.mean(axis=0))
            np.testing.assert_allclose(scaler.scale_,train.std(axis=0))

    def test_saved_predictions_and_independent_metrics(self):
        with (OUT/'predictions.csv').open(encoding='utf-8') as f:
            predictions=list(csv.DictReader(f))
        self.assertEqual(len(predictions),len(self.rows))
        self.assertEqual({r['event_id'] for r in predictions},{r['event_id'] for r in self.rows})
        by_id={r['event_id']:r for r in predictions}
        bundle=joblib.load(OUT/'selected_model.joblib')
        metrics=read(OUT/'metrics.json')
        for split,rs in self.sets.items():
            y=np.array([int(r['goal']) for r in rs])
            for mid,expected in metrics[split].items():
                p=np.array([float(by_id[r['event_id']][mid]) for r in rs])
                self.assertTrue(np.all(np.isfinite(p)&(p>=0)&(p<=1)))
                self.assertAlmostEqual(log_loss(y,np.clip(p,1e-12,1-1e-12)),expected['log_loss'])
                self.assertAlmostEqual(brier_score_loss(y,p),expected['brier_score'])
                self.assertAlmostEqual(roc_auc_score(y,p),expected['roc_auc'])
                self.assertEqual(sum(b['shots'] for b in expected['calibration_bins']),len(rs))
            np.testing.assert_allclose(bundle_probability(bundle,rs),[float(by_id[r['event_id']][bundle['selected_id']]) for r in rs],atol=1e-12)
            # Existing Week 3 reference stays byte-for-byte reproducible in reported scores.
            previous=read(ROOT/'week3/results/metrics.json')[split]['logistic']
            current=metrics[split]['week3_logistic_geometry']
            for key in ['log_loss','brier_score','roc_auc']:
                self.assertAlmostEqual(previous[key],current[key],places=10)

    def test_group_reconciliation(self):
        errors=read(OUT/'error_analysis.json');overall=read(OUT/'metrics.json')
        selected=read(OUT/'selection.json')['selected_id']
        for split,fields in errors.items():
            for field,groups in fields.items():
                for mid in ['week3_logistic_geometry',selected]:
                    self.assertEqual(sum(g[mid]['shots'] for g in groups.values()),overall[split][mid]['shots'])
                    self.assertEqual(sum(g[mid]['goals'] for g in groups.values()),overall[split][mid]['goals'])
                    weighted=sum(g[mid]['log_loss']*g[mid]['shots'] for g in groups.values())/overall[split][mid]['shots']
                    self.assertAlmostEqual(weighted,overall[split][mid]['log_loss'])


if __name__=='__main__':
    unittest.main(verbosity=2)
