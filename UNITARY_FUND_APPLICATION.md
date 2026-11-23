# UNITARY FOUNDATION MICROGRANT APPLICATION
> **Grant Program:** Unitary Fund Microgrant ($4,000.00 USD, Equity-Free)
> **Project Name:** `qiskit-neat-fold`
> **Repository:** https://github.com/kleitonbernardino-lab/qiskit-neat-fold
> **License:** MIT License

## 1. Project Summary
`qiskit-neat-fold` is an open-source Qiskit transpilation and pre-dispatch analysis toolkit providing:
1. **`FoldRzzAnglePass`**: Analytical folding of arbitrary bound $R_{ZZ}(\theta)$ gate angles into $(0, \pi/2]$ via local single-qubit Clifford conjugations ($X, Z$), preserving two-qubit unitary equivalence up to global phase without introducing `GlobalPhaseGate` nodes.
2. **`NeatCliffordPreflight`**: Pre-dispatch static Clifford group membership verification alongside a first-order heuristic attenuation and Quantum Runtime Unit (RU) cost estimator.
3. **`MitigationConflictDetector`**: Local configuration policy checker separating native fractional-gate workflows (Mode A) from Pauli-twirled/PEC workflows (Mode B) and catching contradictory readout mitigation flags.

## 2. Roadmap & Deliverables
- **Milestone 1 (Weeks 1–2):** Live `BackendV2.target` error-rate ingestion with explicit provenance metadata (backend name, calibration timestamp, aggregation method) and active-qubit-only Dynamical Decoupling pruning.
- **Milestone 2 (Weeks 3–4):** Reproducible A/B transpilation and hardware benchmark suite comparing folded vs. unfolded $R_{ZZ}(\theta)$ circuits, published as a versioned PyPI release (`qiskit-neat-fold`).