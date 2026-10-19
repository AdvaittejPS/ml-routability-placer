#!/usr/bin/env python3
"""
Simple MCNC .yal netlist parser (starter implementation).

Outputs canonical JSON with instances and nets.
"""

import argparse
import json
import re


def parse_yal(path):
    text = open(path, 'r').read()
    # remove C-style comments
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    instances = []
    nets = []

    comp_pat = re.compile(r'^COMPONENT\s+(\S+)\s+(\S+)\s+([0-9.]+)\s+([0-9.]+)\s*;?$', re.I)
    for ln in lines:
        m = comp_pat.match(ln)
        if m:
            name, ctype, w, h = m.groups()
            instances.append({"name": name, "type": ctype, "width": float(w), "height": float(h)})

    net_pat = re.compile(r'^([^\s\(]+)\s*\((.*)\)\s*;?$', re.S)
    for ln in lines:
        m = net_pat.match(ln)
        if not m:
            continue
        net_name, body = m.groups()
        tokens = re.split(r'[\s,]+', body.strip())
        pins = []
        for tok in tokens:
            if not tok:
                continue
            if '.' in tok:
                inst, pin = tok.split('.', 1)
            else:
                inst, pin = tok, ''
            pins.append({"instance": inst, "pin": pin})
        nets.append({"name": net_name, "pins": pins})

    if not instances:
        seen = set()
        for net in nets:
            for p in net['pins']:
                seen.add(p['instance'])
        for inst in sorted(seen):
            instances.append({"name": inst, "type": "unknown", "width": 1.0, "height": 1.0})

    return {"instances": instances, "nets": nets}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True)
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args()

    data = parse_yal(args.input)
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Parsed {len(data['instances'])} instances and {len(data['nets'])} nets -> {args.output}")


if __name__ == '__main__':
    main()
