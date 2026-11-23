# qiskit-neat-fold

Topological RZZ(theta) angle folding, zero-RU heuristic attenuation & cost estimation, and runtime options policy validation for Qiskit transpilation workflows.

## Overview

qiskit-neat-fold provides three modular, self-contained utilities:

1. **FoldRzzAnglePass (qiskit_neat_fold.fold_rzz)**: A Qiskit TransformationPass that analytically folds bound RZZ(theta) gate angles into the fundamental domain (0, pi/2] using local single-qubit Clifford conjugations (X, Z). Preserves exact two-qubit unitary equivalence up to global phase (including odd multiples of pi mapped to Z (x) Z and even multiples of pi mapped to identity) without introducing spurious GlobalPhaseGate nodes.
2. **NeatCliffordPreflight (qiskit_neat_fold.preflight)**: A pre-dispatch static analyzer that checks exact Clifford group membership (qiskit.quantum_info.Clifford) and computes a first-order analytical attenuation proxy and Quantum Runtime Unit (RU) cost estimate using reference Heron r2 baseline parameters (or caller-supplied rates via from_backend_rates()).
3. **MitigationConflictDetector (qiskit_neat_fold.conflict_detector)**: A local policy validator for runtime option dictionaries that catches incompatible combinations between native fractional gates (Mode A) and standard Clifford/Pauli-twirled workflows (Mode B), as well as contradictory readout mitigation flags (TREX vs M3).

## Quickstart

    pip install -e ".[dev]"
    pytest -v
    python examples/demo_preflight_and_fold.py

## Scope & Limitations

- NeatCliffordPreflight computes a **first-order heuristic attenuation proxy** from aggregate 1Q, 2Q, and measured-qubit readout error rates; uncompiled 3+ qubit gates use a configurable heuristic multiplier (default 6.0x 2Q gates, not a universal physical decomposition bound). It is not a full density-matrix simulator or logical syndrome survival predictor.
- MitigationConflictDetector enforces **documented local configuration policies** rather than replacing server-side Qiskit Runtime schema validation.

## License

MIT License.
