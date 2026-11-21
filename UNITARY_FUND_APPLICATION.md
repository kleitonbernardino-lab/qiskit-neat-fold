# UNITARY FOUNDATION MICROGRANT APPLICATION DOSSIER
> **Grant Program:** Unitary Fund Microgrant ($4,000.00 USD, Equity-Free)  
> **Project Name:** `qiskit-neat-fold`  
> **Repository:** https://github.com/kleitonbernardino-lab/qiskit-neat-fold  
> **License:** MIT License (100% Open Source)  
> **Application Status:** Ready for Submission

---

## 1. PROJECT TITLE & SUMMARY

### Title
**qiskit-neat-fold: Automated Topological Angle Folding, Zero-RU Pre-flight Clifford Verification, and Mitigation Conflict Detection for IBM Quantum Runtime V2**

### Executive Summary (150 Words)
In contemporary superconducting architectures (such as IBM Quantum Heron r2 156-qubit processors), native cross-resonance and fractional $R_{ZZ}(\theta)$ interactions are physically calibrated over the domain $\theta \in (0, \pi/2]$. Out-of-bounds angles trigger transpiler de-optimizations, excessive CX cascades, and costly runtime dispatch failures. Furthermore, users frequently waste precious Quantum Seconds (RUs) by submitting circuits with severe dephasing or invalid mitigation combinations (e.g., stacking fractional gates with Pauli twirling, or TREX with M3).

`qiskit-neat-fold` is an open-source, lightweight Qiskit transpilation and pre-flight suite that:
1. Analytically folds arbitrary $R_{ZZ}(\theta)$ angles to $(0, \pi/2]$ while preserving exact two-qubit unitary equivalence without introducing spurious `GlobalPhaseGate` nodes;
2. Evaluates Clifford signal retention under calibrated hardware noise at **0.0 RU cost** before hardware dispatch;
3. Statically detects and prevents incompatible error mitigation combinations.

---

## 2. PROBLEM STATEMENT & COMMUNITY IMPACT

### The Problem
With the release of Qiskit 1.x and IBM Quantum Runtime V2, hardware execution has transitioned to instruction set architectures (ISA) utilizing fractional gates (Mode A) and specialized error mitigators. However, developer friction remains high:
- Submitting continuous angles $\theta > \pi/2$ or $\theta < 0$ causes transpilers to synthesize multi-gate decompositions that inflate circuit depth by up to $3\times$.
- New quantum researchers and open-source contributors repeatedly burn limited free-tier and PAYG compute allocations on jobs that decohere into uniform noise.
- Mutually exclusive mitigation options silently distort measurement statistics or cause runtime exceptions.

### Impact on the Quantum Ecosystem
`qiskit-neat-fold` provides:
- **Zero-Waste Pre-flighting:** Saves developer credits by catching decoherence and budget traps locally.
- **Circuit Depth Reduction:** Preserves native pulse synthesis by folding angles analytically into calibrated windows.
- **Ecosystem Integration:** Fully compliant with Qiskit's `StagedPassManager` and `TransformationPass` standards.

---

## 3. PROJECT MILESTONES & DELIVERABLES (3-MONTH PLAN)

### Month 1: Core Engine & Packaging (Completed / Current State)
- [x] Complete analytical proof and implementation of `FoldRzzAnglePass`.
- [x] Implementation of `NeatCliffordPreflight` (0-RU cost estimation & attenuation model).
- [x] Implementation of `MitigationConflictDetector`.
- [x] Comprehensive test suite with 100% unitary equivalence verification.
- [ ] Publish package to PyPI (`pip install qiskit-neat-fold`).

### Month 2: Qiskit Ecosystem Integration & Benchmarking
- [ ] Implement support for parametrized and symbolic circuits (`ParameterExpression`).
- [ ] Integrate with Qiskit Transpiler Plugin architecture (`qiskit.transpiler.plugins`).
- [ ] Run benchmarks against standard Trotterized Hamiltonian dynamics and QAOA instances on Heron processors, publishing depth-reduction metrics.
- [ ] Submit application to the official **IBM Qiskit Ecosystem Catalog**.

### Month 3: Community Tutorials & Documentation
- [ ] Publish an interactive Jupyter notebook walkthrough demonstrating pre-flight savings and angle folding.
- [ ] Host an open community demo / tutorial session on the Unitary Fund Discord.
- [ ] Final project report and release of version 1.0.0.

---

## 4. BUDGET BREAKDOWN (TOTAL: $4,000.00 USD)

| Category | Description | Amount (USD) |
| :--- | :--- | :--- |
| **P&D & Software Engineering** | Implementation of Qiskit transpiler plugin interface, symbolic parameter folding, and CI/CD test automation | **$2,500.00** |
| **Benchmarking & Validation** | Extensive empirical validation across heavy-hex topologies and Trotterized simulation circuits | **$800.00** |
| **Documentation & Tutorials** | Authoring Sphinx documentation, Jupyter notebook tutorials, and Qiskit Ecosystem integration | **$700.00** |
| **Total** | **Equity-Free Non-Dilutive Grant** | **$4,000.00** |

---

## 5. APPLICANT INFORMATION & OPEN SOURCE COMMITMENT

- **Lead Developer:** Kleiton Bernardino / Quantum Open Source Contributor
- **GitHub:** https://github.com/kleitonbernardino-lab
- **Commitment to Open Source:** All code developed under this grant is released under the permissive **MIT License**, with zero proprietary dependencies and complete architectural independence.
