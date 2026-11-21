"""
qiskit-neat-fold: Topological Angle Folding and Zero-RU Pre-flight Verification for IBM Quantum Runtime V2
"""

from .fold_rzz import FoldRzzAnglePass, fold_angle_half_pi
from .preflight import NeatCliffordPreflight, PreflightResult
from .conflict_detector import MitigationConflictDetector, MitigationConflictError

__version__ = "0.1.0"
__all__ = [
    "FoldRzzAnglePass",
    "fold_angle_half_pi",
    "NeatCliffordPreflight",
    "PreflightResult",
    "MitigationConflictDetector",
    "MitigationConflictError",
]
