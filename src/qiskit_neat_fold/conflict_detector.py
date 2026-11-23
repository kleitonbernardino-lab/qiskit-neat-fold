# -*- coding: utf-8 -*-
"""
conflict_detector.py: Local Policy & Options Consistency Validator.

Checks runtime option dictionaries against local policy rules separating Mode A
(native fractional gates) from Mode B (standard basis + Pauli twirling / PEC) and
preventing contradictory readout mitigation flags.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


class MitigationConflictError(Exception):
    """Raised when strict=True and hard policy conflicts exist in runtime options."""
    pass


@dataclass
class InspectionReport:
    """Structured result separating hard conflicts from non-blocking advisories."""
    conflicts: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.conflicts) == 0


def _get_strict_bool(mapping: Dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in mapping or mapping[key] is None:
        return default
    val = mapping[key]
    if not isinstance(val, bool):
        raise TypeError(f"Option '{key}' must be a boolean (True/False), got {type(val).__name__}: {val!r}")
    return val


def _get_strict_dict(mapping: Dict[str, Any], key: str) -> Dict[str, Any]:
    if key not in mapping or mapping[key] is None:
        return {}
    val = mapping[key]
    if not isinstance(val, dict):
        raise TypeError(f"Option '{key}' must be a dictionary, got {type(val).__name__}")
    return val


class MitigationConflictDetector:
    """
    Validates runtime option dictionaries against local policy constraints.
    """

    def __init__(self, strict: bool = True):
        if not isinstance(strict, bool):
            raise TypeError("'strict' must be a boolean.")
        self.strict = strict

    def inspect_report(self, options: Optional[Dict[str, Any]]) -> InspectionReport:
        """
        Evaluates runtime options and returns both hard conflicts and non-blocking warnings.
        """
        if options is None or not isinstance(options, dict):
            raise TypeError("Runtime 'options' must be a valid dictionary.")

        conflicts: List[str] = []
        warnings: List[str] = []

        use_fractional = _get_strict_bool(options, "use_fractional_gates", False)

        twirling = _get_strict_dict(options, "twirling")
        twirling_gates = _get_strict_bool(twirling, "enable_gates", False)
        twirling_measure = _get_strict_bool(twirling, "enable_measure", False)

        resilience = _get_strict_dict(options, "resilience")
        resilience_level = options.get("resilience_level")
        if resilience_level is not None and (isinstance(resilience_level, bool) or not isinstance(resilience_level, int) or resilience_level not in (0, 1, 2, 3)):
            raise ValueError(f"'resilience_level' must be an integer in {{0, 1, 2, 3}}, got {resilience_level!r}")

        zne_enabled = _get_strict_bool(resilience, "zne_mitigation", False) or (resilience_level == 2)
        pec_enabled = _get_strict_bool(resilience, "pec_mitigation", False) or (resilience_level == 3)

        readout_mitigation = _get_strict_bool(options, "readout_mitigation", True)
        use_m3 = _get_strict_bool(options, "use_m3", False)
        use_trex = twirling_measure or _get_strict_bool(options, "use_trex", False)

        # Policy Rule 1: Fractional gates + gate twirling
        if use_fractional and twirling_gates:
            conflicts.append(
                "[CONFLICT - Mode A Policy] 'use_fractional_gates=True' combined with "
                "'twirling.enable_gates=True' violates Mode A local policy: Pauli twirling assumes "
                "Clifford 2Q generators and invalidates continuous fractional angle calibration."
            )

        # Policy Rule 2: Fractional gates + PEC
        if use_fractional and pec_enabled:
            conflicts.append(
                "[CONFLICT - Mode A vs Mode B Policy] Native fractional gates combined with PEC "
                "(Probabilistic Error Cancellation) requires Pauli-Lindblad noise learning over standard basis gates."
            )

        # Advisory Rule 3: Fractional gates + ZNE (non-blocking warning)
        if use_fractional and zne_enabled:
            warnings.append(
                "[ADVISORY - Mode A + ZNE] Combining fractional gates with ZNE (Zero-Noise Extrapolation) "
                "depends on target backend folding/pulse-stretching support; verify noise amplification factors."
            )

        # Policy Rule 4: TREX vs M3 clash
        if use_trex and use_m3:
            conflicts.append(
                "[CONFLICT - Readout Policy] TREX (Twirled Readout) cannot be stacked with M3 "
                "(Matrix-free Measurement Mitigation) because measurement twirling randomizes the readout basis."
            )

        # Policy Rule 5: Contradictory disabled readout mitigation while requesting TREX or M3
        if not readout_mitigation and (use_trex or use_m3):
            conflicts.append(
                "[CONFLICT - Readout Policy] 'readout_mitigation=False' contradicts active "
                "measurement mitigation flags (TREX or M3)."
            )

        if self.strict and conflicts:
            raise MitigationConflictError("\n".join(conflicts))

        return InspectionReport(conflicts=conflicts, warnings=warnings)

    def inspect_options(self, options: Optional[Dict[str, Any]]) -> List[str]:
        """Backward-compatible helper returning hard conflict messages."""
        return self.inspect_report(options).conflicts
