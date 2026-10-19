#!/usr/bin/env python3
"""Robust MCNC YAL parser using block regex.

This version scans MODULE ... ENDMODULE blocks with regex, extracts TYPE,
DIMENSIONS, and IOLIST contents. It also extracts NET lines elsewhere in the
file. This should correctly parse the ami33/ami49 files in the MCNC suite.
"""

import argparse
import json
import os
import re
from typing import Dict, List, Any


def remove_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.S)


def parse_dimensions_str(s: str) -> Dict[str, float]:
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", s)]
    if len(nums) >= 8:
        xs = [nums[0], nums[2], nums[4], nums[6]]
        ys = [nums[1], nums[3], nums[5], nums[7]]
        return {"width": max(xs) - min(xs), "height": max(ys) - min(ys)}
    return {"width": 0.0, "height": 0.0}


def parse_iolist(iolist_text: str) -> List[Dict[str, Any]]:
    pins = []
    for ln in iolist_text.splitlines():
        ln = ln.strip().rstrip(';')
        if not ln:
            continue
        tokens = re.split(r"\s+", ln)
        if len(tokens) < 4:
            continue
        name = tokens[0]
        typ = tokens[1]
        try:
            x = float(tokens[2])
            y = float(tokens[3])
        except Exception:
            x = 0.0
            y = 0.0
        pins.append({"name": name, "type": typ, "x": x, "y": y})
    return pins


def parse_modules(text: str) -> List[Dict[str, Any]]:
    modules = []
    pattern = re.compile(r"MODULE\s+(\S+)\s*;(.*?)(?:ENDMODULE;|ENDMODULE)", re.S | re.I)
    for m in pattern.finditer(text):
        name = m.group(1)
        body = m.group(2)
        module = {"name": name, "type": "unknown", "width": 0.0, "height": 0.0, "pins": []}

        mt = re.search(r"TYPE\s+(\S+)", body, re.I)
        if mt:
            module['type'] = mt.group(1)

        md = re.search(r"DIMENSIONS\s+(.*?);", body, re.I)
        if md:
            dims = parse_dimensions_str(md.group(1))
            module['width'] = dims['width']
            module['height'] = dims['height']

        mi = re.search(r"IOLIST\s*;(.*?)ENDIOLIST\s*;?", body, re.S | re.I)
        if mi:
            module['pins'] = parse_iolist(mi.group(1))

        modules.append(module)
    return modules


def parse_nets(text: str) -> List[Dict[str, Any]]:
    nets = []
    for m in re.finditer(r"(?:NET\s+)?([A-Za-z0-9_\-]+)\s*\((.*?)\)\s*;", text, re.S | re.I):
        name = m.group(1)
        body = m.group(2)
        tokens = re.split(r"[\s,]+", body.strip())
        pins = []
        for tok in tokens:
            tok = tok.strip().rstrip(';,')
            if not tok:
                continue
            if '.' in tok:
                inst, pin = tok.split('.', 1)
                pins.append({"instance": inst, "pin": pin})
            else:
                pins.append({"instance": tok, "pin": ""})
        nets.append({"name": name, "pins": pins})
    return nets


def parse_yal(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        text = f.read()
    text = remove_comments(text)
    modules = parse_modules(text)
    nets = parse_nets(text)

    if not modules and nets:
        seen = set()
        for net in nets:
            for p in net['pins']:
                if p.get('instance'):
                    seen.add(p['instance'])
        modules = [{"name": name, "type": "unknown", "width": 0.0, "height": 0.0, "pins": []} for name in sorted(seen)]

    return {"instances": modules, "nets": nets}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input', required=True)
    ap.add_argument('-o', '--output', required=True)
    args = ap.parse_args()

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    data = parse_yal(args.input)
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Parsed {len(data['instances'])} instances and {len(data['nets'])} nets -> {args.output}")


if __name__ == '__main__':
    main()
