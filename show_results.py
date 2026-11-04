"""Print the pilot results in the same order as the Week 2 slides."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
def load(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
a=load('audit.json');m=load('model_metrics.json');g=load('group_summaries.json')
print('EPL 2015/16 pilot only; not the expanded European/World Cup dataset.')
print(f"Matches={a['selected_matches']}; events={a['all_events']}; shots={a['all_shots']}")
print(f"Non-penalty shots={a['nonpenalty_eligible_shots']}; goals={a['nonpenalty_eligible_goals']}")
print('\nMATCH / SHOT / GOAL SPLITS')
for k,v in m['split_counts'].items():
    print(k, v['matches'], v['shots'], v['goals'])
print('\nPILOT TEST METRICS')
for k,v in m['evaluation']['test'].items():
    print(f"{k}: LogLoss={v['log_loss']:.6f}; Brier={v['brier_score']:.6f}; AUC={v['roc_auc']:.6f}")
print('\nDISTANCE BINS (STATSBOMB UNITS)')
for v in g['groups']['distance_bands_sb_units']:
    print(f"{v['name']}: shots={v['shots']}, goals={v['goals']}, rate={100*v['goal_rate']:.2f}%")
print('\nCALIBRATION BINS')
for v in m['evaluation']['test']['logistic_distance_angle']['calibration_bins']:
    print(f"[{v['lower']:.1f}, {v['upper']:.1f}): n={v['shots']}; predicted={100*v['mean_probability']:.2f}%; observed={100*v['goal_rate']:.2f}%")
