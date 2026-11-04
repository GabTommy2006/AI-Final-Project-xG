"""Independent checks of geometry, leakage boundaries and reproducibility."""
import csv
import math
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

import numpy as np

from pipeline import ROOT, fit, geometry, metrics, predict, read, run, save


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

    def test_saved_results(self):
        out = Path(__file__).parent/'results'
        with (out/'predictions.csv').open(encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        split = read(out/'split_matches.json')
        self.assertFalse(set(split['train']) & set(split['test']))
        self.assertFalse(set(split['train']) & set(split['validation']))
        self.assertFalse(set(split['validation']) & set(split['test']))
        matches = sorted(read(ROOT/'selected_matches.json'), key=lambda m:(m['match_date'], m['match_id']))
        self.assertEqual(sum([split[s] for s in ['train', 'validation', 'test']], []), [m['match_id'] for m in matches])
        self.assertEqual(len({r['event_id'] for r in rows}), len(rows))
        train = [r for r in rows if r['split'] == 'train']
        x = np.array([[float(r['distance_sb_units']), float(r['angle_rad'])] for r in train])
        y = np.array([float(r['goal']) for r in train])
        model = read(out/'model.json')
        np.testing.assert_allclose(model['mean'], x.mean(axis=0))
        np.testing.assert_allclose(model['beta'], fit(x, y)['beta'])
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
        # Regression check against the independently retained Week 2 pilot.
        previous = read(ROOT/'model_metrics.json')['evaluation']['test']['logistic_distance_angle']
        current = read(out/'metrics.json')['test']['logistic']
        for key in ['log_loss', 'brier_score', 'roc_auc']:
            self.assertAlmostEqual(previous[key], current[key], places=10)


if __name__ == '__main__':
    unittest.main()
