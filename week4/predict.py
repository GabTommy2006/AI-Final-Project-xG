"""Predict an eligible non-penalty shot with the validation-selected Week 4 model."""
import argparse
import math
from pathlib import Path
import joblib
from core import ROOT, CATEGORICAL, bundle_probability

def shot_row(x, y, body_part=None, shot_type='Open Play', play_pattern=None, technique=None):
    if not (math.isfinite(x) and math.isfinite(y) and 0<=x<=120 and 0<=y<=80):
        raise ValueError('Coordinates must be finite, x in [0,120], y in [0,80]')
    if x==120 and y in (36,44):
        raise ValueError('Undefined viewing angle at goalpost')
    if shot_type=='Penalty':
        raise ValueError('This model excludes penalties')
    return dict(distance_sb_units=math.hypot(120-x,y-40),
                angle_rad=math.atan2(8*(120-x),(120-x)**2+(y-40)**2-16),
                body_part=body_part,shot_type=shot_type,play_pattern=play_pattern,technique=technique)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--x',type=float,required=True);p.add_argument('--y',type=float,required=True)
    p.add_argument('--body-part');p.add_argument('--shot-type',default='Open Play')
    p.add_argument('--play-pattern');p.add_argument('--technique')
    p.add_argument('--model',type=Path,default=ROOT/'week4/results/selected_model.joblib')
    args=p.parse_args()
    try:
        row=shot_row(args.x,args.y,args.body_part,args.shot_type,args.play_pattern,args.technique)
    except ValueError as exc:
        p.error(str(exc))
    bundle=joblib.load(args.model)
    if bundle['context']:
        missing=[f for f in CATEGORICAL if row[f] is None]
        if missing:
            p.error('Selected contextual model needs: '+', '.join(missing)+'. Supply the observed context.')
        encoder=bundle['model'].named_steps['preprocess'].named_transformers_['context']
        unknown=[f for f,known in zip(CATEGORICAL,encoder.categories_) if row[f] not in known]
        if unknown:
            print('Unseen categories encoded with handle_unknown=ignore: '+', '.join(unknown))
    probability=float(bundle_probability(bundle,[row])[0])
    print(f"Selected model: {bundle['selected_id']}")
    print(f'Non-penalty pre-shot xG: {probability:.6f} ({probability:.2%})')
