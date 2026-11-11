"""Single-shot pre-shot xG prediction in StatsBomb coordinates."""
import argparse
from pathlib import Path
import numpy as np
from pipeline import geometry, predict, read

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--x', type=float, required=True)
    parser.add_argument('--y', type=float, required=True)
    args = parser.parse_args()
    if not (0 <= args.x <= 120 and 0 <= args.y <= 80):
        parser.error('Coordinates must be x in [0,120], y in [0,80]')
    model = read(Path(__file__).parent/'results/model.json')
    try:
        features = geometry(args.x, args.y)
    except ValueError as exc:
        parser.error(str(exc))
    probability = predict(model, np.array([features]))[0]
    print(f'Non-penalty pre-shot xG: {probability:.6f} ({probability:.2%})')
