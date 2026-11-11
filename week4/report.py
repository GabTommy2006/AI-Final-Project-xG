"""Generate source-backed Week 4 plots and report from locked experiment outputs."""
import csv
import os
from pathlib import Path
import joblib
import numpy as np
from core import ROOT, read, save

os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'week4/.mplcache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=ROOT/'week4/results'


def write_csv(path, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    metrics=read(OUT/'metrics.json');selection=read(OUT/'selection.json')
    plan=read(OUT/'experiment_plan.json');search=read(OUT/'validation_search.json')
    baseline='week3_logistic_geometry';chosen=selection['selected_id']
    labels={'constant_train_rate':'Constant',baseline:'LR geometry',
            selection['family_winners']['logistic_context']:'LR context (best)',
            selection['family_winners']['forest_geometry']:'RF geometry (best)',
            selection['family_winners']['forest_context']:'RF context (best)'}
    labels.setdefault('logistic_context_C1','LR context (C=1)')
    rows=[]
    for split,models in metrics.items():
        for model,m in models.items():
            rows.append(dict(split=split,model=model,**{k:m[k] for k in ['shots','goals','log_loss','brier_score','roc_auc','accuracy_at_0_5','f1_at_0_5']}))
    write_csv(OUT/'comparison.csv',rows)
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    ids=list(metrics['validation'])
    fig,ax=plt.subplots(figsize=(10,4.6))
    ax.barh([labels[m] for m in ids],[metrics['validation'][m]['log_loss'] for m in ids],
            color=['#2c7b5a' if m==chosen else '#8ba69a' for m in ids])
    ax.set_xlabel('Validation Log Loss (lower is better)');ax.set_title('Week 4 model selection uses validation only')
    ax.invert_yaxis();fig.tight_layout();fig.savefig(OUT/'validation_comparison.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.6),sharex=True,sharey=True)
    for ax,split in zip(axes,['validation','test']):
        ax.plot([0,1],[0,1],'--',color='gray',label='Perfect calibration')
        for mid,color in [(baseline,'#89958c'),(chosen,'#2c7b5a')]:
            bins=metrics[split][mid]['calibration_bins']
            ax.plot([b['mean_xg'] for b in bins],[b['goal_rate'] for b in bins],'o-',color=color,label=labels.get(mid,mid))
        ax.set_title(split.capitalize());ax.set_xlabel('Mean predicted probability');ax.set_xlim(0,1);ax.set_ylim(0,1)
    axes[0].set_ylabel('Observed goal fraction');axes[1].legend(fontsize=9)
    fig.suptitle('Reliability diagrams: sparse high-probability bins remain uncertain')
    fig.tight_layout();fig.savefig(OUT/'calibration.png',dpi=160);plt.close(fig)
    family_ids=[baseline,*selection['family_winners'].values()]
    x=np.arange(len(family_ids));fig,ax=plt.subplots(figsize=(10,4.8))
    ax.bar(x-.18,[metrics['train'][m]['log_loss'] for m in family_ids],.36,label='Train',color='#a8bdb0')
    ax.bar(x+.18,[metrics['validation'][m]['log_loss'] for m in family_ids],.36,label='Validation',color='#2c7b5a')
    ax.set_xticks(x,[labels[m] for m in family_ids]);ax.set_ylabel('Log Loss');ax.set_title('Train–validation gap by model family');ax.legend()
    fig.tight_layout();fig.savefig(OUT/'generalization_gap.png',dpi=160);plt.close(fig)
    errors=read(OUT/'error_analysis.json');group_rows=[]
    for split,fields in errors.items():
        for field,groups in fields.items():
            for group,item in groups.items():
                b,s=item[baseline],item[chosen]
                group_rows.append(dict(split=split,field=field,group=group,shots=s['shots'],goals=s['goals'],
                    baseline_log_loss=b['log_loss'],selected_log_loss=s['log_loss'],
                    delta_selected_minus_baseline=s['log_loss']-b['log_loss'],small_sample_warning=item['small_sample_warning']))
    write_csv(OUT/'group_errors.csv',group_rows)
    groups=errors['validation']['distance_band'];names=list(groups);xx=np.arange(len(names))
    fig,ax=plt.subplots(figsize=(8,4.5))
    ax.bar(xx-.18,[groups[g][baseline]['log_loss'] for g in names],.36,label='LR geometry',color='#a8bdb0')
    ax.bar(xx+.18,[groups[g][chosen]['log_loss'] for g in names],.36,label='Selected',color='#2c7b5a')
    ax.set_xticks(xx,[g+'\nn='+str(groups[g][chosen]['shots']) for g in names]);ax.set_ylabel('Validation Log Loss')
    ax.set_xlabel('Distance band (StatsBomb units)');ax.set_title('Error analysis by distance');ax.legend()
    fig.tight_layout();fig.savefig(OUT/'distance_errors.png',dpi=160);plt.close(fig)
    bundle=joblib.load(OUT/'selected_model.joblib')
    if bundle['kind']=='sklearn':
        model=bundle['model'].named_steps['model']
        features=bundle['model'].named_steps['preprocess'].get_feature_names_out().tolist()
        if hasattr(model,'coef_'):
            save(OUT/'selected_explanation.json',dict(model=chosen,intercept=float(model.intercept_[0]),
                coefficient_units='Numeric slopes use train-standardized inputs; context slopes use one-hot indicators. Associations, not causal effects.',
                coefficients=dict(zip(features,model.coef_[0].tolist()))))
        else:
            save(OUT/'selected_explanation.json',dict(model=chosen,
                impurity_importance_not_causal=dict(zip(features,model.feature_importances_.tolist()))))
    lines=['# Week 4 — Model Development & Evaluation','',
        'Actual experiment results on the unchanged Week 3 non-penalty dataset. No CNN/LSTM was trained.', '',
        '## Data and protocol','',
        '2,411 matches; 59,519 eligible shots; 6,074 goals. Same whole-match chronological split: '
        'train 35,559 shots, validation 11,909, test 12,051. No resampling or class weighting.', '',
        'Pre-shot model inputs: distance and angle; contextual variants additionally use body part, shot type, play pattern and technique. '
        'Outcome is target only. Provider xG, end location, future events and match/player identities are not inputs.', '',
        'Input CSV SHA-256: `'+plan['input_sha256']+'`.', '',
        '## Architecture, training and hyperparameters','',
        'Frozen baseline: Week 3 standardized two-feature logistic, unpenalized intercept and fixed L2=1. '
        'Library geometry logistic C=1 reproduces its predictions; see baseline_parity.json.', '',
        'Context logistic: train-fitted numeric StandardScaler plus one-hot categorical encoding; unknown categories are ignored and missing '
        'values have an explicit marker. L2 logistic uses C in {0.1, 1, 10}; lbfgs, max_iter=2000, tol=1e-10. '
        'It optimizes regularized binary negative log likelihood; C is inverse regularization.', '',
        'Random Forest: geometry-only and context variants. 200 bootstrap trees, sqrt features per split, '
        'Gini split criterion, depth in {6, 10, unlimited}, min_samples_leaf in {20, 50}, random_state=2026. '
        'Gini measures node impurity; it is not the logistic training objective. Forest probability averages class probabilities across trees.', '',
        'Fifteen predeclared candidate configurations plus the frozen baseline compete on validation Log Loss; Brier then ID break ties. '
        'The plan is written before fitting, validation search is saved, and selection is locked before any new candidate test scores are computed. '
        'The selected model stays fitted on train only, preserving comparability. No post-hoc calibration model was fitted.', '',
        '## Selected model','',f"Selected: **{chosen}**, parameters `{selection['params']}`.", '',
        'Selection was made by validation performance, not by which model looks best on test. '
        'A contextual C=1 logistic is also reported as a matched-regularization control for the feature comparison.', '',
        '## Validation and reported test metrics','']
    for split in ['validation','test']:
        for mid,m in metrics[split].items():
            lines.append(f"- {split}, {mid}: Log Loss {m['log_loss']:.6f}; Brier {m['brier_score']:.6f}; ROC-AUC {m['roc_auc']:.6f}.")
    for split in ['validation','test']:
        b,s=metrics[split][baseline],metrics[split][chosen]
        lines.extend(['',f"Selected-minus-baseline {split} Log Loss: {s['log_loss']-b['log_loss']:+.6f}; "
                      f"Brier: {s['brier_score']-b['brier_score']:+.6f}. Negative loss differences are improvements on this split."])
    lines.extend(['','Accuracy and F1 are supplementary at fixed threshold 0.5 (see comparison.csv). '
        'No threshold was optimized; these are not the primary xG criteria. Log Loss clipping is 1e-12, matching Week 3. '
        'AUC is ranking, not accuracy; probability losses mix discrimination and calibration.', '',
        '## Error analysis and observed challenges',''])
    for mid in family_ids:
        gap=metrics['validation'][mid]['log_loss']-metrics['train'][mid]['log_loss']
        lines.append(f'- {mid}: validation-minus-train Log Loss gap {gap:+.6f}.')
    for split in ['validation','test']:
        m=metrics[split][chosen];bins=m['calibration_bins'];high=sum(b['shots'] for b in bins if b['lower']>=.5)
        lines.append(f"- {split} selected model: mean xG {100*m['mean_xg']:.2f}%, observed goals {100*m['goal_rate']:.2f}%; "
                     f"{high} shots in bins at xG >= 0.5. Similar global means do not prove calibration.")
    # Discover validation weaknesses, explicitly labeled as diagnostics after selection.
    worst=sorted([r for r in group_rows if r['split']=='validation' and not r['small_sample_warning']],
                 key=lambda r:r['delta_selected_minus_baseline'],reverse=True)[:5]
    lines.append('');lines.append('Largest selected-minus-baseline validation Log Loss differences among groups with >=100 shots and >=10 goals:')
    for r in worst:
        lines.append(f"- {r['field']}={r['group']}: n={r['shots']}, goals={r['goals']}, delta={r['delta_selected_minus_baseline']:+.6f}.")
    lines.extend(['','These are overlapping descriptive groups, not independent hypothesis tests. '
        'Small groups are flagged in group_errors.csv. No significance or universal superiority claim is made.', '',
        'Coverage is unbalanced and chronology changes competition composition. Both World Cups and Euros are only in test. '
        'There are no new missing-label or coordinate imputations; Week 3 cleaning is reused. Missing/unseen categorical values are audited. '
        'The contextual forest has a larger train–validation gap than the simple baseline; inspect the actual values rather than equating complexity with quality.', '',
        '## Improvement plan and Week 5','',
        'Keep the validation-selected model for the demo. In Week 5, integrate input validation and contextual inputs, probability display '
        'and shot visualization; provide run instructions and final reporting. Consider interaction features or calibration only under a '
        'newly specified train/validation protocol; do not use reported test scores to select another candidate.', '',
        'The Week 3 test was already inspected before this experiment. These test scores are transparent retrospective reporting, '
        'not an untouched final holdout. Independent data/protocol is required before an untouched-evaluation claim. '
        'No independent new dataset was collected in Week 4.', '',
        '## Evidence and progress','',
        'See experiment_plan.json, validation_search.json, selection.json, comparison.csv, predictions.csv, error_analysis.json, '
        'preprocessing_audit.json, selected_model.joblib and validation.json. Plots are reproducibly generated by report.py.', '',
        'Owner: Phuc Hung, sole contributor. Planned Week 4 budget: 14 hours from the prior WBS. Actual student hours: not supplied; '
        'gap cannot yet be calculated. runtime.json measures script execution time only, not student effort. '
        'Tutor feedback and personal issue/time logs must be recorded honestly.', '',
        'Data source: StatsBomb Open Data (Hudl), pinned source manifest inherited from Week 3. '
        'This is a student model, not provider xG. Raw events and Python environments remain excluded from Git.', ''])
    (OUT/'SUMMARY.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f"Generated report and plots. Selected model: {chosen}")


if __name__=='__main__':
    main()
