# Experimental Context & Evidence Manifest — Deltakit Community Fund (Issue #437)

## Scope & Implementation Status
- **Package:** `qiskit-neat-fold` (`v0.1.0`)
- **Implemented & Unit-Tested Capabilities (Current Release):**
  1. `FoldRzzAnglePass`: Exact analytical angle folding for bound $R_{ZZ}(\theta)$ gates into $(0, \pi/2]$ using local single-qubit Clifford conjugations ($X, Z$), mapping odd multiples of $\pi$ to $Z \otimes Z$ and even multiples of $\pi$ to identity up to global phase.
  2. `NeatCliffordPreflight`: Zero-RU pre-dispatch static analyzer combining exact Clifford group membership checks (`qiskit.quantum_info.Clifford`) with a first-order heuristic attenuation & RU cost proxy.
  3. `MitigationConflictDetector`: Local policy validator separating Mode A (native fractional gates) from Mode B (standard Clifford/Pauli-twirled workflows) and flagging contradictory readout mitigation options.

## Separate Experimental Context (IBM Quantum Telemetry)
*Note: The telemetry below served as empirical motivation for the roadmap milestones; it is not presented as a direct hardware validation of the heuristic preflight estimator or RZZ folding pass.*
- **Context Dataset:** 15 physical QPU jobs (86 PUBs / Primitive Unified Blocs, 105.0 s QPU charge time) executed during hardware characterization experiments on `ibm_kingston` (Heron r2).
- **Reference Job (`dc1s1c5hdvas73bl97e0`):** `ibm_kingston`, `2026-11-23T04:27:28Z`, `0.099868 RU` across 4 batched PUBs (`circuit_sha256`: `38405f6b1ba8495c12930470fa1843dcd025b3d86553d12aef41f469207e082b`).
- **Observed Hardware Motivation for M1:** Unpruned `PadDynamicalDecoupling` inserted 154 spectator `delay` instructions on a 2-qubit active PUB (`92.77%` spectator DD overhead), motivating active-qubit-only DD pruning in Milestone 1.

## Proposed Grant Roadmap (Future Deliverables)
- **M1:** Live `BackendV2.target` calibration ingestion into `NeatCliffordPreflight` and active-qubit-only DD pruning pass.
- **M2:** Controlled hardware A/B benchmark of folded vs unfolded fractional $R_{ZZ}$ circuits on IBM Heron r2 and Deltakit QEC syndrome-extraction pipelines.