"""Generate presentation evidence from the actual expanded run, not hardcoded scores."""
from pathlib import Path
from pipeline import read

HERE = Path(__file__).parent


def main():
    audit = read(HERE/'results/data_audit.json')
    scores = read(HERE/'results/metrics.json')
    split = read(HERE/'results/split_summary.json')
    coverage = read(HERE/'data/coverage.json')
    lines = ['# Week 3 expanded baseline — actual results', '',
        f"Source revision: `{audit['source_snapshot']['git_commit']}`.", '',
        f"Selected {audit['selected_matches']:,} matches across {len(coverage)} competition-seasons, "
        f"{audit['first_date']} to {audit['last_date']}.", '',
        f"Raw: {audit['counts']['all_events']:,} events and {audit['counts']['all_shots']:,} shots. "
        f"Retained: {audit['retained_shots']:,} non-penalty shots, {audit['goals']:,} goals.", '',
        '## Cleaning exclusions', '']
    for key, value in audit['counts'].items():
        if key not in ['all_events', 'all_shots']:
            lines.append(f'- {key}: {value:,}.')
    lines.extend(['', '## Match-disjoint chronological split', ''])
    for name, item in split.items():
        lines.append(f"- {name}: {item['matches']:,} matches, {item['shots']:,} shots, "
                     f"{item['goals']:,} goals; {item['first_date']} to {item['last_date']}.")
    lines.extend(['', '## Baseline metrics', ''])
    for name, models in scores.items():
        for model, item in models.items():
            auc = f"{item['roc_auc']:.6f}" if item['roc_auc'] is not None else 'undefined (one class)'
            lines.append(f"- {name}, {model}: log loss {item['log_loss']:.6f}; "
                         f"Brier {item['brier_score']:.6f}; ROC-AUC {auc}.")
    lines.extend(['', '## Coverage and interpretation limits', '',
        'All available matches satisfying the scope at this source revision were downloaded. '
        'Open-data coverage is incomplete relative to real competition schedules: these are not all '
        'European matches since 2001. Champions League entries are selected finals, and many seasons '
        'are team/player-focused samples. World Cup coverage here is 2018 and 2022.', '',
        'The expanded scores use a different population and split from the Week 2 pilot. Do not claim '
        'model improvement by comparing these scores directly with the old pilot. Training is still '
        'the same fixed distance/angle logistic baseline.', '',
        'Chronological splitting changes competition composition over time. Inspect split_summary.json '
        'and competition_metrics.json before interpreting pooled scores. Sparse groups and calibration '
        'bins are uncertain; no confidence interval or statistical superiority claim is made.', '',
        'With this split, both World Cup editions appear only in test, not training. Their scores '
        'measure transfer from the earlier European training sample rather than within-World-Cup validation.', '',
        'This test has now been inspected for baseline reporting. Week 4 selection must use validation; '
        'an independent evaluation is needed for an untouched final performance claim.', '',
        'Data attribution: StatsBomb Open Data (Hudl). Follow the source LICENSE.pdf and README '
        'when using or publishing data/results. Raw event JSON is not committed.', ''])
    (HERE/'results/SUMMARY.md').write_text('\n'.join(lines), encoding='utf-8')
    lines = ['# Available in-scope coverage at the pinned source revision', '',
             'Counts are available public matches, not a claim of full-season coverage.', '']
    for item in sorted(coverage, key=lambda c:(c['competition'], c['first_date'])):
        lines.append(f"- {item['competition']} — {item['season']}: {item['selected_matches']} matches "
                     f"({item['first_date']} to {item['last_date']}).")
    (HERE/'data/COVERAGE.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
