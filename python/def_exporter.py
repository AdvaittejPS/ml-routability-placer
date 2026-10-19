#!/usr/bin/env python3
"""
Simple DEF exporter for macro placements. Input: placement JSON or CSV with instance,x,y
Outputs minimal DEF with MACRO PLACEMENT lines.
"""

import argparse
import json


def load_placement(path):
    # accept JSON with list of {'name','x','y'}
    try:
        data = json.load(open(path))
        if isinstance(data, dict) and 'placements' in data:
            return data['placements']
        # heuristic: if list
        if isinstance(data, list):
            return data
    except Exception:
        pass
    # fallback: try CSV
    placements = []
    with open(path) as f:
        for ln in f:
            tok = ln.strip().split(',')
            if len(tok) < 3:
                continue
            placements.append({'name': tok[0], 'x': float(tok[1]), 'y': float(tok[2])})
    return placements


def write_def(placements, out_path, die_area=(0,0,1000,1000)):
    with open(out_path, 'w') as f:
        f.write('VERSION 1.0 ;\n')
        f.write(f'DIVIDERCHAR "/" ;\n')
        f.write('BUSBITCHARS "[]" ;\n')
        f.write('DIEAREA ( {} {} ) ( {} {} ) ;\n'.format(*die_area))
        f.write('COMPONENTS {} ;\n'.format(len(placements)))
        for p in placements:
            f.write(f'  - {p["name"]} + PLACED ( {int(p["x"])} {int(p["y"])} ) N ;\n')
        f.write('END COMPONENTS\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--placement', required=True)
    parser.add_argument('-o', '--def', required=True)
    args = parser.parse_args()

    placements = load_placement(args.placement)
    write_def(placements, args.def)
    print(f'Wrote DEF to {args.def}')

if __name__ == '__main__':
    main()
