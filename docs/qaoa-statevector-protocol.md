# QAOA Statevector Protocol & Mixer Synthesis

## Parameterized Layers
For depth $p$:
$$|\gamma, \beta\rangle = \prod_{k=1}^p e^{-i \beta_k H_M} e^{-i \gamma_k H_C} |+\rangle^{\otimes n}$$

- **Cost Hamiltonian $H_C$:** Diagonal in computational basis representing QUBO quadratic terms.
- **Mixer Hamiltonian $H_M$:** Transverse field $\sum_j X_j$ enabling quantum interference between computational states.
