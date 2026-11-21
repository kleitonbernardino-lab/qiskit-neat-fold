# Hamiltonian Reduction & Pauli Operator Grouping

## Overview
This document specifies the grouping strategies for Hamiltonian observables into mutually commuting subsets:
1. **Qubit-Wise Commuting (QWC):** Fast $O(N^2)$ greedy coloring where operators commute on every individual qubit index.
2. **General Commuting (GC):** Unitary transformation via Clifford circuits into simultaneous eigenbases.

## Complexity Bounds
- Maximum measurement circuits for $M$ Pauli terms: bounded by chromatic number $\chi(G_{comm})$.
- Circuit depth overhead: $O(N^2 / \log N)$ for full Clifford diagonalizer synthesis.
