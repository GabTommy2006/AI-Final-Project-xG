"""Independent checks of geometry, leakage boundaries and reproducibility."""
import csv
import math
from pathlib import Path
import unittest
import tempfile
import gzip
import hashlib
from unittest.mock import patch

import numpy as np

from pipeline import ROOT, fit, geometry, metrics, predict, read, run, save
from scope import eligible_catalogue_entry, eligible_match


class BaselineTests(unittest.TestCase):
    def test_geometry(self):
        distance, angle = geometry(108, 40)
        self.assertAlmostEqual(distance, 12)
        self.assertAlmostEqual(angle, 2*math.atan(4/12))
        self.assertEqual(geometry(100, 30), geometry(100, 50))
        for point in [(120, 36), (120, 44), (float('nan'), 40), (-1, 40)]:
            with self.assertRaises(ValueError):
                geometry(*point)

    def test_cleaning_and_duplicate_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            matches = []
            for mid in range(1, 6):
                matches.append(dict(match_id=mid, match_date=f'2015-08-0{mid}',
                                    competition=dict(country_name='England', competition_name='Premier League'),
                                    home_team=dict(home_team_gender='male'), away_team=dict(away_team_gender='male')))
                events = [dict(id=f'{mid}-{i}', type=dict(name='Shot'), period=1, location=[108, 40],
                               shot=dict(type=dict(name='Open Play'), outcome=dict(name=outcome)))
                          for i, outcome in enumerate(['Goal', 'Saved'])]
                if mid == 1:
                    for i, kind in enumerate(['penalty', 'shootout', 'location', 'outcome', 'post', 'id']):
                        event = dict(id=f'bad-{i}', type=dict(name='Shot'), period=1, location=[100, 40],
                                     shot=dict(type=dict(name='Open Play'), outcome=dict(name='Saved')))
                        if kind == 'penalty': event['shot']['type']['name'] = 'Penalty'
                        if kind == 'shootout': event['period'] = 5
                        if kind == 'location': event['location'] = [121, 40]
                        if kind == 'outcome': event['shot'].pop('outcome')
                        if kind == 'post': event['location'] = [120, 36]
                        if kind == 'id': event.pop('id')
                        events.append(event)
                save(root/f'events_{mid}.json', events)
            save(root/'matches.json', matches)
            with patch('builtins.print'):
                run(root/'matches.json', root, root/'results')
            audit = read(root/'results/data_audit.json')
            self.assertEqual(audit['retained_shots'], 10)
            self.assertEqual(audit['counts']['all_shots'], 16)
            self.assertEqual(sum(v for k, v in audit['counts'].items() if k not in ['all_events', 'all_shots']), 6)
            manifest = [dict(match_id=mid, sha256=hashlib.sha256((root/f'events_{mid}.json').read_bytes()).hexdigest()) for mid in range(1, 6)]
            save(root/'manifest.json', manifest)
            payload = (root/'events_5.json').read_bytes()
            (root/'events_5.json.gz').write_bytes(gzip.compress(payload))
            (root/'events_5.json').unlink()
            with patch('builtins.print'):
                run(root/'matches.json', root, root/'compressed-results', root/'manifest.json')
            self.assertEqual(read(root/'compressed-results/data_audit.json')['retained_shots'], 10)
            manifest[0]['sha256'] = 'bad-hash'
            save(root/'manifest.json', manifest)
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                run(root/'matches.json', root, root/'corrupt-results', root/'manifest.json')
            events = read(root/'events_1.json')
            events.append(events[0])
            save(root/'events_1.json', events)
            with self.assertRaisesRegex(ValueError, 'Duplicate Shot ID'):
                run(root/'matches.json', root, root/'duplicate-results')

    def test_probability_metrics(self):
        y = np.array([0., 1.])
        result = metrics(y, np.array([.5, .5]))
        self.assertAlmostEqual(result['log_loss'], math.log(2))
        self.assertEqual(result['brier_score'], .25)
        self.assertEqual(result['roc_auc'], .5)
        self.assertEqual(metrics(y, np.array([0., 1.]))['roc_auc'], 1.)
        rng = np.random.default_rng(42)
        labels = rng.integers(0, 2, 200).astype(float)
        probs = rng.integers(0, 10, 200)/10
        positive, negative = probs[labels == 1], probs[labels == 0]
        pairwise = np.mean([(np.sum(p > negative)+.5*np.sum(p == negative))/len(negative) for p in positive])
        self.assertAlmostEqual(metrics(labels, probs)['roc_auc'], pairwise)

    def test_scope_policy(self):
        for country, competition, expected in [('Europe', 'Champions League', True),
                ('Europe', 'UEFA Euro', True), ('International', 'FIFA World Cup', True),
                ('United States of America', 'Major League Soccer', False),
                ('South America', 'Copa America', False)]:
            comp = dict(country_name=country, competition_name=competition,
                        competition_gender='male', competition_youth=False)
            self.assertEqual(eligible_catalogue_entry(comp), expected)
            self.assertFalse(eligible_catalogue_entry(dict(comp, competition_gender='female')))
            self.assertFalse(eligible_catalogue_entry(dict(comp, competition_youth=True)))
        m = dict(match_date='2001-01-01', competition=dict(country_name='England'),
                 home_team=dict(home_team_gender='male'), away_team=dict(away_team_gender='male'))
        self.assertTrue(eligible_match(m))
        self.assertFalse(eligible_match(dict(m, match_date='2000-12-31')))

    def test_saved_results(self):
        out = Path(__file__).parent/'results'
        with (out/'predictions.csv').open(encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        split = read(out/'split_matches.json')
        self.assertFalse(set(split['train']) & set(split['test']))
        self.assertFalse(set(split['train']) & set(split['validation']))
        self.assertFalse(set(split['validation']) & set(split['test']))
        matches = sorted(read(ROOT/'week3/data/selected_matches.json'), key=lambda m:(m['match_date'], m['match_id']))
        self.assertEqual(sum([split[s] for s in ['train', 'validation', 'test']], []), [m['match_id'] for m in matches])
        self.assertEqual(len(split['train']), int(.6*len(matches)))
        self.assertEqual(len(split['validation']), int(.8*len(matches))-int(.6*len(matches)))
        self.assertEqual(len({r['event_id'] for r in rows}), len(rows))
        train = [r for r in rows if r['split'] == 'train']
        x = np.array([[float(r['distance_sb_units']), float(r['angle_rad'])] for r in train])
        y = np.array([float(r['goal']) for r in train])
        model = read(out/'model.json')
        np.testing.assert_allclose(model['mean'], x.mean(axis=0))
        np.testing.assert_allclose(model['scale'], x.std(axis=0))
        np.testing.assert_allclose(model['beta'], fit(x, y)['beta'])
        design = np.column_stack([np.ones(len(x)), (x-np.array(model['mean']))/np.array(model['scale'])])
        penalty_gradient = np.array(model['beta'])*np.array([0., 1., 1.])
        gradient = design.T@(predict(model, x)-y)+penalty_gradient
        self.assertLess(float(np.max(np.abs(gradient))), 1e-4)
        for s in split:
            subset = [r for r in rows if r['split'] == s]
            self.assertTrue(all(int(r['match_id']) in split[s] for r in subset))
            features = np.array([[float(r['distance_sb_units']), float(r['angle_rad'])] for r in subset])
            np.testing.assert_allclose(predict(model, features), [float(r['xg']) for r in subset])
            target = np.array([float(r['goal']) for r in subset])
            actual = metrics(target, predict(model, features))
            expected = read(out/'metrics.json')[s]['logistic']
            for key in ['log_loss', 'brier_score', 'roc_auc']:
                self.assertAlmostEqual(actual[key], expected[key])
            constant = metrics(target, np.full(len(subset), float(y.mean())))
            expected_constant = read(out/'metrics.json')[s]['constant']
            for key in ['log_loss', 'brier_score', 'roc_auc']:
                self.assertAlmostEqual(constant[key], expected_constant[key])
        audit = read(out/'data_audit.json')
        self.assertEqual(audit['retained_shots'], len(rows))
        self.assertEqual(audit['selected_matches'], len(matches))
        manifest = read(ROOT/'week3/data/source_manifest.json')
        self.assertEqual({m['match_id']:m['sha256'] for m in manifest},
                         {m['match_id']:m['sha256'] for m in audit['source_manifest']})
        self.assertTrue(all(eligible_match(m) for m in matches))
        counts = audit['counts']
        excluded = sum(v for k, v in counts.items() if k not in ['all_events', 'all_shots'])
        self.assertEqual(counts['all_shots'], len(rows)+excluded)
        status = read(ROOT/'week3/data/download_status.json')
        self.assertEqual(status['failures'], [])
        self.assertEqual(status['success'], len(matches))
        coverage = read(ROOT/'week3/data/coverage.json')
        catalogue = read(ROOT/'week3/data/competitions.json')
        expected_seasons = {(c['competition_id'], c['season_id']) for c in catalogue
                            if eligible_catalogue_entry(c) and int(c['season_name'][-4:]) >= 2001}
        self.assertEqual(expected_seasons, {(c['competition_id'], c['season_id']) for c in coverage})
        self.assertEqual(sum(c['selected_matches'] for c in coverage), len(matches))

    def test_pilot_regression(self):
        # The expanded evaluation is different; the original pilot must still reproduce.
        previous = read(ROOT/'model_metrics.json')['evaluation']['test']['logistic_distance_angle']
        pilot_matches = read(ROOT/'selected_matches.json')
        raw = ROOT/'raw'
        if not all((raw/f"events_{m['match_id']}.json").exists() for m in pilot_matches):
            raw = ROOT/'raw/week3'
        with tempfile.TemporaryDirectory() as folder, patch('builtins.print'):
            run(ROOT/'selected_matches.json', raw, Path(folder))
            current = read(Path(folder)/'metrics.json')['test']['logistic']
        for key in ['log_loss', 'brier_score', 'roc_auc']:
            self.assertAlmostEqual(previous[key], current[key], places=10)


if __name__ == '__main__':
    unittest.main()
