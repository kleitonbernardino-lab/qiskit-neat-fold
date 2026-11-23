# Evidence Manifest — Deltakit Community Fund (Issue #437)

## Scope & Scientific Alignment
- **Package:** `qiskit-neat-fold` (`v0.1.0`)
- **Core Capabilities:**
  1. `FoldRzzAnglePass`: Exact unitary angle folding for native fractional $R_{ZZ}(\theta)$ gates into $(0, \pi/2]$ using local single-qubit Clifford conjugations ($X, Z$).
  2. `NeatCliffordPreflight`: Zero-RU pre-dispatch analytical Pauli-Lindblad attenuation & RU cost estimator with exact `Clifford` membership verification and explicit calibration baselines.
  3. `MitigationConflictDetector`: Static compatibility validator preventing Mode A (Fractional Gates) vs Mode B (Pauli Twirling / PEC / ZNE) and TREX vs M3 configuration clashes.

## Verified IBM Quantum Telemetry (Sanitized)
- **Dataset:** 15 physical QPU jobs, 86 PUBs, 105.0 s total QPU charge time (`1.643304 RUs`) across 3 calibrated backends (`ibm_kingston` Heron r2).
- **Reference Job ID:** `dc1s1c5hdvas73bl97e0` (`ibm_kingston`, `2026-11-23T04:27:28Z`, `0.099868 RU` across 4 batched PUBs, `circuit_sha256`: `38405f6b1ba8495c12930470fa1843dcd025b3d86553d12aef41f469207e082b`).
- **Key Empirical Finding Driving Milestone 1:** Standard `PadDynamicalDecoupling` without spectator pruning generated `154` spectator `delay` ops per 2-qubit active PUB (`92.77%` spectator DD overhead; `88,886` wasted ops across 15 jobs) and `2.1508 s` mean per-job charge overhead.
- **Zero-RU Parity/Syndrome Purification Benchmark (`dc1s1c5hdvas73bl97e0`):**
  - 2Q Bell (`PUB0`): Raw fidelity `0.989502` -> Mitigated/$\mathbb{Z}_2$-purified `0.999874`.
  - 5Q GHZ (`PUB1`): Raw fidelity `0.933350` -> Mitigated/$\mathbb{Z}_2$-purified `0.987571`.
  - 7Q Ring (`PUB2`): Raw fidelity `0.896484` -> Mitigated/$\mathbb{Z}_2$-purified `0.970232`.

## Roadmap Milestones (Grant Scope)
- **M1:** Live `BackendV2.target` calibration ingestion into `NeatCliffordPreflight` and active-qubit-only DD pruning pass.
- **M2:** Hardware A/B benchmark of folded vs unfolded fractional $R_{ZZ}$ circuits on IBM Heron r2 & Deltakit QEC syndrome-extraction pipelines.
