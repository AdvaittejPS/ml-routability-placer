# ML-driven Routability-Aware Macro Placement Engine

This repository contains an end-to-end undergraduate-level MVP for a routability-aware macro placer. The goal is to provide a working pipeline from MCNC netlists (.yal) → parsed canonical JSON → feature extraction & SVM training → a lightweight C++ placer that integrates an ML congestion penalty → DEF exporter and OpenROAD integration scripts.

Quickstart

1. Clone the repo
   git clone https://github.com/AdvaittejPS/ml-routability-placer.git
   cd ml-routability-placer

2. Python environment
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r python/requirements.txt

3. Parse a netlist (toy example included)
   python3 python/parser/mcnc_parser.py -i python/parser/example_ami33.yal -o data/processed/ami33.json

4. Build C++ skeleton
   mkdir -p build && cd build
   cmake ../cpp
   cmake --build . -- -j
   ./placer_cli ../data/processed/ami33.json

Repository layout

- README.md (this file)
- .gitignore
- cpp/
  - CMakeLists.txt
  - include/ (headers)
  - src/ (sources)
- python/
  - requirements.txt
  - parser/
    - mcnc_parser.py
    - example_ami33.yal
  - ml/
    - train_svm.py
  - def_exporter.py
- scripts/
  - run_openroad.sh
- data/
  - raw/ and processed/
- docs/
  - next_steps.md

Notes and limitations

- The included parser is a starter and may need tweaks to support all MCNC variants. Paste a small sample if your .yal differs.
- The C++ placer is a runnable skeleton implementing LSE-smoothed HPWL, a fast kernel-based density approximation, and a hook for ML congestion penalty (loads JSON model). It is designed to be extended.

