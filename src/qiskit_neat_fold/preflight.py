# -*- coding: utf-8 -*-
"""
preflight.py: Zero-RU Heuristic Pre-Dispatch Circuit Attenuation & Cost Estimator.

Provides a first-order heuristic attenuation proxy and Quantum Runtime Unit (RU) cost
estimator alongside exact Clifford group membership checks before hardware dispatch.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford
from qiskit.exceptions import QiskitError


def _validate_probability(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite float, got {value!r}")
    if not (0.0 <= float(value) <= 1.0):
        raise ValueError(f"{name} must be within [0.0, 1.0], got {value!r}")
    return float(value)


def _validate_non_negative_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer, got {value!r}")
    return value


def estimate_circuit_attenuation(
    depth: int,
    num_1q: int,
    num_2q: int,
    num_measured_qubits: int = 0,
    num_3plus_q: int = 0,
    multi_qubit_weight: float = 6.0,
    shots: int = 4096,
    avg_1q_error: float = 0.0003,
    avg_2q_error: float = 0.0025,
    avg_readout_error: float = 0.015,
    ru_rate_per_sec: float = 1.0 / 60.0,
    retention_threshold: float = 0.40,
    calibration_source: str = "heron_r2_reference_baseline",
    is_clifford: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Single-source-of-truth first-order heuristic attenuation & RU cost model.

    Heuristic proxy convention:
        R_est = exp(-(N_1q * e_1q + N_2q_eff * e_2q)) * (1 - e_ro)^min(N_meas_qubits, 10)
    where uncompiled 3+ qubit gates are weighted by a configurable heuristic multiplier
    (default 6.0x 2Q gates, representing a textbook Toffoli-to-CX synthesis heuristic rather
    than a universal bound), and readout decay scales only with measured qubits (capped at 10).
    """
    depth = _validate_non_negative_int("depth", depth)
    num_1q = _validate_non_negative_int("num_1q", num_1q)
    num_2q = _validate_non_negative_int("num_2q", num_2q)
    num_measured_qubits = _validate_non_negative_int("num_measured_qubits", num_measured_qubits)
    num_3plus_q = _validate_non_negative_int("num_3plus_q", num_3plus_q)
    if (
        isinstance(multi_qubit_weight, bool)
        or not isinstance(multi_qubit_weight, (int, float))
        or not math.isfinite(multi_qubit_weight)
        or multi_qubit_weight < 1.0
    ):
        raise ValueError(f"multi_qubit_weight must be a finite number >= 1.0, got {multi_qubit_weight!r}")
    if isinstance(shots, bool) or not isinstance(shots, int) or shots < 1:
        raise ValueError(f"shots must be a positive integer >= 1, got {shots!r}")

    avg_1q_error = _validate_probability("avg_1q_error", avg_1q_error)
    avg_2q_error = _validate_probability("avg_2q_error", avg_2q_error)
    avg_readout_error = _validate_probability("avg_readout_error", avg_readout_error)
    retention_threshold = _validate_probability("retention_threshold", retention_threshold)

    if (
        isinstance(ru_rate_per_sec, bool)
        or not isinstance(ru_rate_per_sec, (int, float))
        or not math.isfinite(ru_rate_per_sec)
        or ru_rate_per_sec < 0.0
    ):
        raise ValueError(f"ru_rate_per_sec must be a non-negative finite number, got {ru_rate_per_sec!r}")

    effective_2q = num_2q + (float(multi_qubit_weight) * num_3plus_q)
    exponent = (num_1q * avg_1q_error) + (effective_2q * avg_2q_error)
    gate_decay = math.exp(-exponent)
    readout_decay = (1.0 - avg_readout_error) ** min(num_measured_qubits, 10)
    estimated_retention = float(max(0.0, min(1.0, gate_decay * readout_decay)))

    circuit_duration_us = (depth * 1.2) + 120.0
    total_time_sec = (circuit_duration_us * 1e-6 * shots) + 1.5
    estimated_ru = total_time_sec * float(ru_rate_per_sec)
    is_viable = estimated_retention >= retention_threshold

    warnings: List[str] = []
    recommendations: List[str] = []

    if num_3plus_q > 0:
        warnings.append(
            f"Uncompiled multi-qubit gates detected ({num_3plus_q} gate(s) with >=3 qubits): "
            f"weighted by heuristic multiplier ({multi_qubit_weight}x 2Q gates each). "
            "Transpile to target ISA before final estimation."
        )

    if is_clifford is False:
        warnings.append(
            "Non-Clifford circuit detected: retention score is a first-order heuristic "
            "attenuation proxy rather than exact stabilizer survival."
        )

    if not is_viable:
        warnings.append(
            f"High attenuation warning: Estimated signal retention ({estimated_retention:.2%}) "
            f"falls below threshold ({retention_threshold:.2%}). Depth={depth}, 2Q gates={num_2q}."
        )
        recommendations.append("Apply circuit compression, angle folding, or reduce ansatz entanglement depth.")
    else:
        recommendations.append(f"Circuit passes heuristic pre-dispatch check ({calibration_source}).")

    if shots > 4096:
        warnings.append(
            f"Shot budget warning: {shots} shots requested. Shots above 4096 may exhibit diminishing "
            "returns under hardware bias floors while increasing RU consumption."
        )
        recommendations.append("Consider setting shots=4096 unless active mitigation requires higher variance resolution.")

    if effective_2q > 250:
        recommendations.append(
            "High two-qubit gate count (>250): Ensure Dynamical Decoupling (DD XY4) is enabled on active qubits."
        )

    return {
        "is_viable": is_viable,
        "is_clifford": is_clifford,
        "estimated_retention": round(estimated_retention, 6),
        "estimated_retention_percent": f"{estimated_retention * 100:.2f}%",
        "depth": depth,
        "num_1q_gates": num_1q,
        "num_2q_gates": num_2q,
        "num_3plus_q_gates": num_3plus_q,
        "num_measured_qubits": num_measured_qubits,
        "estimated_duration_sec": round(total_time_sec, 6),
        "estimated_ru_cost": round(estimated_ru, 6),
        "calibration_source": calibration_source,
        "warnings": warnings,
        "recommendations": recommendations,
    }


@dataclass
class PreflightResult:
    """Pre-dispatch heuristic estimation outcome."""
    is_viable: bool
    is_clifford: bool
    estimated_retention: float
    depth: int
    num_1q_gates: int
    num_2q_gates: int
    num_3plus_q_gates: int
    num_measured_qubits: int
    estimated_duration_sec: float
    estimated_ru_cost: float
    calibration_source: str = "heron_r2_reference_baseline"
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class NeatCliffordPreflight:
    """Evaluates quantum circuits using a first-order heuristic attenuation proxy at 0.0 RU cost."""

    def __init__(
        self,
        avg_1q_error: float = 0.0003,
        avg_2q_error: float = 0.0025,
        avg_readout_error: float = 0.015,
        ru_rate_per_sec: float = 1.0 / 60.0,
        retention_threshold: float = 0.40,
        multi_qubit_weight: float = 6.0,
        calibration_source: str = "heron_r2_reference_baseline",
    ):
        self.avg_1q_error = _validate_probability("avg_1q_error", avg_1q_error)
        self.avg_2q_error = _validate_probability("avg_2q_error", avg_2q_error)
        self.avg_readout_error = _validate_probability("avg_readout_error", avg_readout_error)
        if (
            isinstance(ru_rate_per_sec, bool)
            or not isinstance(ru_rate_per_sec, (int, float))
            or not math.isfinite(ru_rate_per_sec)
            or ru_rate_per_sec < 0.0
        ):
            raise ValueError(f"ru_rate_per_sec must be non-negative and finite, got {ru_rate_per_sec!r}")
        if (
            isinstance(multi_qubit_weight, bool)
            or not isinstance(multi_qubit_weight, (int, float))
            or not math.isfinite(multi_qubit_weight)
            or multi_qubit_weight < 1.0
        ):
            raise ValueError(f"multi_qubit_weight must be >= 1.0, got {multi_qubit_weight!r}")
        self.ru_rate_per_sec = float(ru_rate_per_sec)
        self.retention_threshold = _validate_probability("retention_threshold", retention_threshold)
        self.multi_qubit_weight = float(multi_qubit_weight)
        self.calibration_source = calibration_source

    @classmethod
    def from_backend_rates(
        cls,
        avg_1q_error: float,
        avg_2q_error: float,
        avg_readout_error: float,
        backend_name: str = "custom_backend",
        timestamp_utc: Optional[str] = None,
        aggregation_method: str = "caller_supplied",
        retention_threshold: float = 0.40,
        multi_qubit_weight: float = 6.0,
    ) -> "NeatCliffordPreflight":
        """Constructs an estimator populated with caller-supplied backend error rates and provenance."""
        ts_tag = f"@{timestamp_utc}" if timestamp_utc else ""
        source_label = f"user_supplied:{backend_name}{ts_tag}({aggregation_method})"
        return cls(
            avg_1q_error=avg_1q_error,
            avg_2q_error=avg_2q_error,
            avg_readout_error=avg_readout_error,
            retention_threshold=retention_threshold,
            multi_qubit_weight=multi_qubit_weight,
            calibration_source=source_label,
        )

    @staticmethod
    def check_is_clifford(circuit: QuantumCircuit) -> bool:
        """Checks whether the unitary circuit (ignoring final measurements) lies in the Clifford group."""
        try:
            stripped = circuit.remove_final_measurements(inplace=False)
            Clifford(stripped)
            return True
        except QiskitError:
            return False

    def evaluate(self, circuit: QuantumCircuit, shots: int = 4096) -> PreflightResult:
        """Performs static structural, Clifford membership, and heuristic attenuation analysis."""
        if not isinstance(circuit, QuantumCircuit):
            raise TypeError(f"Expected QuantumCircuit, got {type(circuit).__name__}")

        depth = circuit.depth()
        is_clifford = self.check_is_clifford(circuit)

        non_unitary_ops = {"barrier", "measure", "reset", "delay"}
        num_1q = 0
        num_2q = 0
        num_3plus_q = 0
        measured_qubits = set()

        for inst in circuit.data:
            name = inst.operation.name
            if name == "measure":
                for q in inst.qubits:
                    measured_qubits.add(circuit.find_bit(q).index)
                continue
            if name in non_unitary_ops:
                continue
            q_len = len(inst.qubits)
            if q_len == 1:
                num_1q += 1
            elif q_len == 2:
                num_2q += 1
            elif q_len >= 3:
                num_3plus_q += 1

        num_measured_qubits = len(measured_qubits)

        metrics = estimate_circuit_attenuation(
            depth=depth,
            num_1q=num_1q,
            num_2q=num_2q,
            num_measured_qubits=num_measured_qubits,
            num_3plus_q=num_3plus_q,
            multi_qubit_weight=self.multi_qubit_weight,
            shots=shots,
            avg_1q_error=self.avg_1q_error,
            avg_2q_error=self.avg_2q_error,
            avg_readout_error=self.avg_readout_error,
            ru_rate_per_sec=self.ru_rate_per_sec,
            retention_threshold=self.retention_threshold,
            calibration_source=self.calibration_source,
            is_clifford=is_clifford,
        )

        return PreflightResult(
            is_viable=metrics["is_viable"],
            is_clifford=is_clifford,
            estimated_retention=metrics["estimated_retention"],
            depth=depth,
            num_1q_gates=num_1q,
            num_2q_gates=num_2q,
            num_3plus_q_gates=num_3plus_q,
            num_measured_qubits=num_measured_qubits,
            estimated_duration_sec=metrics["estimated_duration_sec"],
            estimated_ru_cost=metrics["estimated_ru_cost"],
            calibration_source=self.calibration_source,
            warnings=metrics["warnings"],
            recommendations=metrics["recommendations"],
        )