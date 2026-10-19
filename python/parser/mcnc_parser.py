#!/usr/bin/env python3
"""Robust MCNC YAL parser.

This parser is intended for the classic MCNC benchmark YAL files (ami33, ami49,
apt, hp, xerox, etc.). It handles the benchmark "MODULE" blocks used in the
YAL floorplanning format and extracts the module name, type, dimensions, and
I/O pins. It also parses NET-style connectivity if present.

Output format:
{
  "instances": [
    {
      "name": "bk1",
      "type": "GENERAL",
      "width": 336.0,
      "height": 133.0,
      "pins": [
        {"name": "P_0", "type": "PWR", "x": 175.0, "y": 0.0},
        ...
      ]
    }
  ],
  "nets": [
    {"name": "NET1", "pins": [{"instance": "U1", "pin": "P1"}, ...]}
  ]
}
"""

import argparse
import json
import os
import re
from typing import List, Dict, Any


def clean_lines(text: str) -> List[str]:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        lines.append(line)
    return lines


def parse_dimensions(dim_str: str) -> Dict[str, float]:
    # Typical MCNC YAL DIMENSIONS: 336 0 336 133 0 133 0 0
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", dim_str)]
    if len(nums) < 8:
        return {"width": 0.0, "height": 0.0}
    xs = [nums[0], nums[2], nums[4], nums[6]]
    ys = [nums[1], nums[3], nums[5], nums[7]]
    return {
        "width": max(xs) - min(xs),
        "height": max(ys) - min(ys),
    }


def parse_pin_tokens(tokens: List[str]) -> Dict[str, Any]:
    # Example token sequences from MCNC YAL:
    #   P_0 PWR 175 0 1 METAL2 CURRENT 0.003 VOLTAGE 2.000
    #   P_2 B 336 14 1 METAL2
    if len(tokens) < 5:
        return {}

    pin_name = tokens[0]
    pin_type = tokens[1] if len(tokens) > 1 and tokens[1].isalpha() else "B"
    try:
        x = float(tokens[2])
        y = float(tokens[3])
    except ValueError:
        return {}

    out = {"name": pin_name, "type": pin_type, "x": x, "y": y}
    return out


def parse_module_block(lines: List[str], start_idx: int):
    """Parse a single MODULE block starting at index start_idx."""
    if start_idx >= len(lines):
        return None, start_idx

    mod_match = re.match(r"^MODULE\s+([^;\s]+)\s*;?", lines[start_idx], re.I)
    if not mod_match:
        return None, start_idx

    name = mod_match.group(1)
    module = {
        "name": name,
        "type": "unknown",
        "width": 0.0,
        "height": 0.0,
        "pins": [],
    }

    idx = start_idx + 1
    in_iolist = False

    while idx < len(lines):
        line = lines[idx]

        if line.upper().startswith("ENDMODULE"):
            return module, idx + 1

        if line.upper().startswith("TYPE"):
            m = re.match(r"^TYPE\s+([^;\s]+)", line, re.I)
            if m:
                module["type"] = m.group(1)

        elif line.upper().startswith("DIMENSIONS"):
            m = re.match(r"^DIMENSIONS\s+(.*?);?\s*$", line, re.I)
            if m:
                dims = parse_dimensions(m.group(1))
                module["width"] = dims["width"]
                module["height"] = dims["height"]

        elif line.upper().startswith("IOLIST"):
            in_iolist = True

        elif in_iolist and line.upper() == "ENDIOLIST":
            in_iolist = False

        elif in_iolist:
            clean = line.rstrip(';')
            tokens = re.split(r"\s+", clean)
            if not tokens:
                idx += 1
                continue
            pin = parse_pin_tokens(tokens)
            if pin:
                module["pins"].append(pin)

        idx += 1

    return module, idx


def parse_generic_net(line: str):
    """Parse a line like: NET1 ( U1.P1 U2.P2 ); or NET n1 ( ... ) ;"""
    m = re.match(r"^(?:NET\s+)?([A-Za-z0-9_\-]+)\s*\((.*)\)\s*;?$", line, re.I)
    if not m:
        return None
    name, body = m.groups()
    tokens = re.split(r"[\s,]+", body.strip())
    pins = []
    for tok in tokens:
        tok = tok.rstrip(';,')
        if not tok:
            continue
        if '.' in tok:
            inst, pin = tok.split('.', 1)
            pins.append({"instance": inst, "pin": pin})
        else:
            pins.append({"instance": tok, "pin": ""})
    return {"name": name, "pins": pins}


def parse_yal(path: str) -> Dict[str, Any]:
    with open(path, "r") as f:
        text = f.read()

    lines = clean_lines(text)
    instances: List[Dict[str, Any]] = []
    nets: List[Dict[str, Any]] = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]

        if line.upper().startswith("MODULE"):
            mod, next_idx = parse_module_block(lines, idx)
            if mod is not None:
                instances.append({
                    "name": mod["name"],
                    "type": mod["type"],
                    "width": mod["width"],
                    "height": mod["height"],
                    "pins": mod["pins"],
                })
            idx = next_idx
            continue

        # Generic NET style lines can appear outside explicit module blocks.
        net = parse_generic_net(line)
        if net is not None:
            nets.append(net)

        idx += 1

    # If no module blocks were found, infer instance names from nets.
    if not instances and nets:
        seen_names = set()
        for net in nets:
            for pin in net["pins"]:
                inst = pin.get("instance")
                if inst:
                    seen_names.add(inst)
        for name in sorted(seen_names):
            instances.append({
                "name": name,
                "type": "unknown",
                "width": 0.0,
                "height": 0.0,
                "pins": [],
            })

    return {"instances": instances, "nets": nets}


def main():
    parser = argparse.ArgumentParser(description="Parse MCNC YAL benchmark netlists")
    parser.add_argument("-i", "--input", required=True, help="input YAL file")
    parser.add_argument("-o", "--output", required=True, help="output JSON file")
    args = parser.parse_args()

    out_dir = os.path.dirname(os.path.abspath(args.output))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    data = parse_yal(args.input)
    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Parsed {len(data['instances'])} instances and {len(data['nets'])} nets -> {args.output}")


if __name__ == "__main__":
    main()
