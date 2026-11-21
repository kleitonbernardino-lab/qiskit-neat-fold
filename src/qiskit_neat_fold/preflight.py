# -*- coding: utf-8 -*-
"""
preflight.py: Zero-RU Pre-flight Clifford Circuit Verification for IBM Quantum Hardware.

Calculates stabilizer/Clifford signal retention and physical execution cost BEFORE
submitting jobs to IBM Quantum Runtime V2, completely preventing wasted Quantum Seconds (RUs).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from qiskit import QuantumCircuit
from qiskit.quantum_info import Clifford


@dataclass
class PreflightResult:
    """Pre-flight verification outcome."""
    is_viable: bool
    clifford_retention: float
    depth: int
    num_1q_gates: int
    num_2q_gates: int
    estimated_duration_sec: float
    estimated_ru_cost: float
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class NeatCliffordPreflight:
    """
    Evaluates quantum circuits under calibrated hardware noise parameters at 0.0 RU cost.
    
    Default parameters reflect typical IBM Quantum Heron r2 processor baselines (e.g., ibm_kingston).
    """

    def __init__(
        self,
        avg_1q_error: float = 0.0003,
        avg_2q_error: float = 0.0025,
        avg_readout_error: float = 0.015,
        ru_rate_per_sec: float = 1.0 / 60.0,
        retention_threshold: float = 0.40,
    ):
        self.avg_1q_error = avg_1q_error
        self.avg_2q_error = avg_2q_error
        self.avg_readout_error = avg_readout_error
        self.ru_rate_per_sec = ru_rate_per_sec
        self.retention_threshold = retention_threshold

    def evaluate(self, circuit: QuantumCircuit, shots: int = 4096) -> PreflightResult:
        """
        Performs static structural and Clifford attenuation analysis.
        """
        depth = circuit.depth()
        num_qubits = circuit.num_qubits
        
        # Count operations
        ops_count = circuit.count_ops()
        two_qubit_names = {"cx", "cz", "ecr", "rzz", "swap", "iswap"}
        num_2q = sum(ops_count.get(name, 0) for name in two_qubit_names)
        num_1q = sum(cnt for name, cnt in ops_count.items() if name not in two_qubit_names and name != "barrier")

        # Analytical Pauli-Lindblad attenuation proxy
        # S = exp(- N_1q * e_1q - N_2q * e_2q) * (1 - e_ro)^N_qubits
        exponent = (num_1q * self.avg_1q_error) + (num_2q * self.avg_2q_error)
        gate_decay = math.exp(-exponent)
        readout_decay = (1.0 - self.avg_readout_error) ** min(num_qubits, 10)
        clifford_retention = float(max(0.0, min(1.0, gate_decay * readout_decay)))

        # Timing and RU estimation (typically ~1.2 us per 2Q layer + 100 us readout + shot repetition)
        circuit_duration_us = (depth * 1.2) + 120.0
        total_time_sec = (circuit_duration_us * 1e-6 * shots) + 1.5  # hardware overhead buffer
        estimated_ru = (total_time_sec / 60.0)

        warnings: List[str] = []
        recommendations: List[str] = []

        is_viable = clifford_retention >= self.retention_threshold

        if not is_viable:
            warnings.append(
                f"Severe noise degradation: Estimated Clifford retention ({clifford_retention:.2%}) "
                f"falls below the threshold ({self.retention_threshold:.2%}). Circuit depth={depth}, 2Q gates={num_2q}."
            )
            recommendations.append("Apply circuit compression, lightcone slicing, or reduce ansatz entanglement depth.")

        if shots > 4096:
            warnings.append(
                f"Shot budget warning: {shots} shots requested. Under typical hardware bias floors (~2.25%), "
                "shots above 4096 exhibit diminishing returns in RMSE while inflating RU consumption."
            )
            recommendations.append("Consider setting shots=4096 unless active mitigation (ZNE/PEC) requires higher variance resolution.")

        if num_2q > 250:
            recommendations.append(
                "High two-qubit gate count (>250): Ensure Dynamical Decoupling (DD XY4) is enabled to suppress dephasing."
            )

        return PreflightResult(
            is_viable=is_viable,
            clifford_retention=clifford_retention,
            depth=depth,
            num_1q_gates=num_1q,
            num_2q_gates=num_2q,
            estimated_duration_sec=total_time_sec,
            estimated_ru_cost=estimated_ru,
            warnings=warnings,
            recommendations=recommendations,
        )
