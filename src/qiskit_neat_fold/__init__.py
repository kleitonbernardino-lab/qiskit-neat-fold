# -*- coding: utf-8 -*-
"""qiskit-neat-fold: Topological angle folding, heuristic preflight, and options policy checks."""

from .fold_rzz import FoldRzzAnglePass, fold_angle_half_pi
from .preflight import NeatCliffordPreflight, PreflightResult, estimate_circuit_attenuation
from .conflict_detector import MitigationConflictDetector, MitigationConflictError, InspectionReport

__version__ = "0.1.0"
__all__ = [
    "FoldRzzAnglePass",
    "fold_angle_half_pi",
    "NeatCliffordPreflight",
    "PreflightResult",
    "estimate_circuit_attenuation",
    "MitigationConflictDetector",
    "MitigationConflictError",
    "InspectionReport",
]
