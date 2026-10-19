# Next steps and development plan to start implementing the MCNC placer

This document provides an ordered checklist and recommended implementation plan to go from the current skeleton to a working C++ placer integrated with the Python ML pipeline.

1) Verify parser on real MCNC netlists
- Run python/parser/mcnc_parser.py on your target .yal (ami33.yal or ami49.yal) placed under data/raw/.
- If the parser misses fields or the format differs, paste a small excerpt here and I will update the parser quickly.

2) Define canonical in-memory data structures in C++
- Instance struct: name, type, width, height, x, y
- Net struct: name, list of pins (instance name, pin name)
- Design struct: bounding box, list of instances, list of nets

3) Implement smoothed HPWL (LSE) and gradient
- For a net with pin coordinates (x_i, y_i), smoothed HPWL via log-sum-exp.
- Compute analytic derivative w.r.t. each pin position. For macros, treat pin offsets from macro origin.

4) Implement fast approximate density penalty
- For MVP, use kernel-based repulsive force instead of solving Poisson.

5) Optimizer: Nesterov or simple Adam-lite

6) Python ML pipeline
- Snapshot generator: perturb placements (random jitter + a few HPWL-only gradient steps)
- Feature extractor: for each grid window compute pin density, cell area density, net traversal count
- Label generation: use FastRoute quick run to get a congestion map, or use heuristic labels for MVP
- Train scikit-learn SVM (RBF) and export support vectors, dual coefficients, intercept, gamma to JSON

7) Integrate SVM into C++ objective
- Evaluate per-window congestion score
- Compute spatial gradient and convert to per-macro penalty forces

8) DEF exporter and OpenROAD integration
- Export DEF for the current placement
- Provide run script using OpenROAD Docker image to run FastRoute/TritonRoute and export DRC logs

9) Validation and experiments
- Run baseline HPWL-only placer and ML-augmented placer
- Run OpenROAD on both DEFs and compare DRC counts

