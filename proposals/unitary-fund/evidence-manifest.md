# Evidence Manifest — Unitary Foundation Microgrant

## Scope & Scientific Alignment
- **Project:** `qiskit-neat-fold` (`v0.1.0`)
- **Core Capabilities:**
  - Exact analytical folding of bound $R_{ZZ}(\theta)$ angles to $(0, \pi/2]$ without spurious `GlobalPhaseGate` nodes.
  - Pre-dispatch static Clifford group membership check and first-order heuristic attenuation/RU cost proxy.
  - Local policy validation for error-mitigation option dictionaries (`InspectionReport` separating hard conflicts from non-blocking advisories).
- **Verification:** Automated test suite verifying unitary equivalence (including singular points $\pm\pi, \pm 3\pi, \pm 2\pi$ and $\pi \pm 10^{-9}$ neighborhoods), strict numeric/boolean input validation, and API/library single-source consistency.