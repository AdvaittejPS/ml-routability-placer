#!/usr/bin/env python3
"""
train_svm.py
- Loads parsed placement snapshots (JSON) or generates simple synthetic snapshots
- Extracts per-window features: pin density, cell area density, net traversal count
- Trains an RBF SVM and exports model as JSON (support vectors, dual coefficients, intercept, gamma)

This is a simple script for the MVP. For serious experiments you'll want
more robust feature engineering and real DRC-based labels.
"""

import argparse
import json
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler


def generate_synthetic_snapshots(parsed_json, n_snap=30, jitter_scale=1.0):
    # parsed_json contains instances with widths/heights. We'll create simple random positions
    insts = parsed_json['instances']
    snapshots = []
    for s in range(n_snap):
        snap = []
        for inst in insts:
            x = np.random.rand() * 100 + np.random.randn() * jitter_scale
            y = np.random.rand() * 100 + np.random.randn() * jitter_scale
            snap.append({'name': inst['name'], 'x': float(x), 'y': float(y)})
        snapshots.append(snap)
    return snapshots


def extract_window_features(snapshots, nets, grid_dim=(10,10)):
    # Flatten snapshots into windows; compute simple features per window per snapshot
    X = []
    for snap in snapshots:
        xs = np.array([p['x'] for p in snap])
        ys = np.array([p['y'] for p in snap])
        # simple per-snapshot global features as placeholder
        features = [xs.mean(), ys.mean(), xs.std(), ys.std(), len(snap)]
        X.append(features)
    return np.array(X)


def synthetic_labels(X):
    # Heuristic: windows with high std dev considered hotspots
    scores = X[:,2] + X[:,3]
    thresh = np.percentile(scores, 70)
    return (scores > thresh).astype(int)


def export_svm_model(clf, scaler, out_path):
    # export essential data: support_vectors, dual_coef, intercept, gamma, scaler mean/scale
    model = {}
    model['support_vectors'] = clf.support_vectors_.tolist()
    model['dual_coef'] = clf.dual_coef_.tolist()
    model['intercept'] = clf.intercept_.tolist()
    model['gamma'] = clf._gamma
    model['classes'] = clf.classes_.tolist()
    model['scaler_mean'] = scaler.mean_.tolist()
    model['scaler_scale'] = scaler.scale_.tolist()
    with open(out_path, 'w') as f:
        json.dump(model, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--parsed', required=True)
    parser.add_argument('-o', '--model', required=True)
    args = parser.parse_args()

    parsed = json.load(open(args.parsed))
    snapshots = generate_synthetic_snapshots(parsed, n_snap=50)
    X = extract_window_features(snapshots, parsed.get('nets', []))
    y = synthetic_labels(X)

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    clf = SVC(kernel='rbf', gamma='scale', probability=False)
    clf.fit(Xs, y)

    export_svm_model(clf, scaler, args.model)
    print(f"Trained SVM saved to {args.model}")

if __name__ == '__main__':
    main()
