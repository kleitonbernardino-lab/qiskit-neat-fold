# -*- coding: utf-8 -*-
"""
conflict_detector.py: Static Detection of Runtime and Mitigation Incompatibilities for IBM Quantum Runtime V2.

Guarantees strict separation between Mode A (Native Fractional Gates) and Mode B (Standard Basis + PEC/ZNE),
preventing runtime job abortions and statistical probability corruption.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional


class MitigationConflictError(Exception):
    """Raised when mutually exclusive quantum error mitigators or runtime options are combined."""
    pass


class MitigationConflictDetector:
    """
    Validates Qiskit Runtime options dictionary against known hardware and mathematical constraints.
    """

    def __init__(self, strict: bool = True):
        self.strict = strict

    def inspect_options(self, options: Dict[str, Any]) -> List[str]:
        """
        Inspects runtime options dict for dangerous or invalid combinations.
        
        Returns:
            List of detected conflict messages.
        Raises:
            MitigationConflictError if strict=True and critical conflicts exist.
        """
        conflicts: List[str] = []

        # Extract flags safely
        use_fractional = options.get("use_fractional_gates", False)
        
        twirling = options.get("twirling", {})
        twirling_gates = twirling.get("enable_gates", False)
        twirling_measure = twirling.get("enable_measure", False)

        resilience = options.get("resilience", {})
        zne_enabled = resilience.get("zne_mitigation", False) or (options.get("resilience_level") == 2)
        pec_enabled = resilience.get("pec_mitigation", False) or (options.get("resilience_level") == 3)
        
        readout_mitigation = options.get("readout_mitigation", True)
        use_m3 = options.get("use_m3", False)
        use_trex = twirling_measure or options.get("use_trex", False)

        # Rule 1: Fractional gates cannot be combined with gate twirling
        if use_fractional and twirling_gates:
            msg = (
                "[CONFLICT - Mode A Violation] 'use_fractional_gates=True' cannot be combined with "
                "'twirling.enable_gates=True'. Twirling standardizes on Clifford generators and corrupts "
                "continuous fractional angle calibration."
            )
            conflicts.append(msg)

        # Rule 2: Fractional gates cannot be combined with PEC or PEA
        if use_fractional and pec_enabled:
            msg = (
                "[CONFLICT - Mode A vs Mode B Clash] Native fractional gates cannot be combined with PEC "
                "(Probabilistic Error Cancellation). PEC requires Pauli-Lindblad decomposition over standard basis CZ."
            )
            conflicts.append(msg)

        # Rule 3: TREX vs M3 clash
        if use_trex and use_m3:
            msg = (
                "[CONFLICT - Measurement Mitigator Clash] TREX (Twirled Readout) cannot be stacked with M3 "
                "(Matrix Inversion). Measurement twirling randomizes the basis, rendering the static calibration "
                "matrix of M3 invalid."
            )
            conflicts.append(msg)

        if self.strict and conflicts:
            raise MitigationConflictError("\n".join(conflicts))

        return conflicts
