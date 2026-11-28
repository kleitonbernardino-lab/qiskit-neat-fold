# -*- coding: utf-8 -*-
"""
fold_rzz.py: TransformationPass for analytical folding of RZZ angles to (0, pi/2].

Folds bounded RZZ parameters analytically into (0, pi/2] using local single-qubit
Clifford conjugations (X, Z), preserving two-qubit unitary equivalence up to global
phase within the configured numerical tolerance `tol` without introducing GlobalPhaseGate nodes.
"""

from __future__ import annotations
import math
from typing import Tuple
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.dagcircuit import DAGCircuit
from qiskit.circuit.library import RZZGate, ZGate, XGate
from qiskit.circuit import ParameterExpression

MAX_TOLERANCE = 1e-8
MIN_TOLERANCE = 1e-13
MAX_ANGLE_MAGNITUDE = 32.0 * math.pi  # ulp(32*pi) ~= 1.42e-14 << 1e-12


def fold_angle_half_pi_with_phase(theta: float, tol: float = 1e-12) -> Tuple[float, bool, bool, bool, float]:
    """
    Folds an angle theta (with |theta| <= 32*pi, ensuring float64 ulp <= 1.42e-14 << tol) into (0, pi/2],
    also returning the exact global phase shift `phase_shift` (radians) such that:
        RZZ(theta) == exp(i * phase_shift) * folded_circuit_unitary.

    Uses IEEE-754 `math.remainder(theta, 2*pi)` to avoid subtractive cancellation for tiny angles.
    """
    if isinstance(theta, bool) or not isinstance(theta, (int, float)) or not math.isfinite(theta):
        raise ValueError(f"Angle theta must be a finite real number, got {theta!r}")
    if abs(theta) > MAX_ANGLE_MAGNITUDE:
        raise ValueError(
            f"Angle magnitude |theta|={abs(theta):.3e} exceeds safe float64 modulo-2pi range ({MAX_ANGLE_MAGNITUDE:.3e})."
        )
    if (
        isinstance(tol, bool)
        or not isinstance(tol, (int, float))
        or not math.isfinite(tol)
        or tol < MIN_TOLERANCE
        or tol > MAX_TOLERANCE
    ):
        raise ValueError(f"Tolerance tol must be within [{MIN_TOLERANCE}, {MAX_TOLERANCE}], got {tol!r}")

    tau = 2.0 * math.pi
    norm_theta = math.remainder(theta, tau)
    k_turns = round((theta - norm_theta) / tau)
    phase_shift = math.pi if (k_turns % 2) != 0 else 0.0

    # Canonicalize -pi to +pi (adjusting phase by pi since RZZ(-pi) = -RZZ(+pi))
    if abs(norm_theta + math.pi) < tol:
        norm_theta = math.pi
        phase_shift = (phase_shift + math.pi) % tau

    if abs(norm_theta) < tol:
        return 0.0, False, False, True, phase_shift

    neg = False
    if norm_theta < 0.0:
        norm_theta = -norm_theta
        neg = True

    reflected = False
    if norm_theta > (math.pi / 2.0) + tol:
        norm_theta = math.pi - norm_theta
        reflected = True
        # RZZ(+a) = -i (Z x Z) X0 RZZ(pi-a) X0  -> phase -pi/2
        # RZZ(-a) = +i (Z x Z) RZZ(pi-a)        -> phase +pi/2
        phase_shift = (phase_shift + (math.pi / 2.0 if neg else -math.pi / 2.0)) % tau

    if abs(norm_theta) < tol:
        return 0.0, False, True, False, phase_shift

    norm_theta = max(tol, min(math.pi / 2.0, norm_theta))
    return float(norm_theta), neg, reflected, False, phase_shift


def fold_angle_half_pi(theta: float, tol: float = 1e-12) -> Tuple[float, bool, bool, bool]:
    """
    Folds an angle theta (with |theta| <= 32*pi, ensuring float64 ulp <= 1.42e-14 << tol) into (0, pi/2].

    Angles within `tol` of 2*k*pi are treated as identity; angles within `tol` of
    (2*k+1)*pi are mapped to the singular Z (x) Z Clifford operation (up to global phase).
    """
    folded_theta, neg, reflected, is_id, _ = fold_angle_half_pi_with_phase(theta, tol=tol)
    return folded_theta, neg, reflected, is_id


class FoldRzzAnglePass(TransformationPass):
    """Transpiler transformation pass that folds bound RZZGate parameters to (0, pi/2]."""

    def __init__(self, target_tolerance: float = 1e-12):
        super().__init__()
        if (
            isinstance(target_tolerance, bool)
            or not isinstance(target_tolerance, (int, float))
            or not math.isfinite(target_tolerance)
            or target_tolerance < MIN_TOLERANCE
            or target_tolerance > MAX_TOLERANCE
        ):
            raise ValueError(f"target_tolerance must be within [{MIN_TOLERANCE}, {MAX_TOLERANCE}], got {target_tolerance!r}")
        self.target_tolerance = float(target_tolerance)

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        for node in dag.op_nodes():
            if node.op.name != "rzz":
                continue
            params = node.op.params
            if not params:
                continue
            param = params[0]

            if isinstance(param, ParameterExpression) and param.parameters:
                continue

            try:
                theta_val = float(param)
            except (TypeError, ValueError):
                continue

            folded_theta, neg, reflected, is_id, phase_shift = fold_angle_half_pi_with_phase(
                theta_val, tol=self.target_tolerance
            )
            if phase_shift:
                dag.global_phase = (float(dag.global_phase) + phase_shift) % (2.0 * math.pi)

            sub_dag = DAGCircuit()
            q0 = node.qargs[0]
            q1 = node.qargs[1]
            sub_dag.add_qubits([q0, q1])

            if is_id:
                dag.substitute_node_with_dag(node, sub_dag)
                continue

            if reflected and folded_theta == 0.0:
                sub_dag.apply_operation_back(ZGate(), qargs=[q0])
                sub_dag.apply_operation_back(ZGate(), qargs=[q1])
                dag.substitute_node_with_dag(node, sub_dag)
                continue

            if neg and reflected:
                sub_dag.apply_operation_back(ZGate(), qargs=[q0])
                sub_dag.apply_operation_back(ZGate(), qargs=[q1])
                sub_dag.apply_operation_back(RZZGate(folded_theta), qargs=[q0, q1])
            elif reflected:
                sub_dag.apply_operation_back(ZGate(), qargs=[q0])
                sub_dag.apply_operation_back(ZGate(), qargs=[q1])
                sub_dag.apply_operation_back(XGate(), qargs=[q0])
                sub_dag.apply_operation_back(RZZGate(folded_theta), qargs=[q0, q1])
                sub_dag.apply_operation_back(XGate(), qargs=[q0])
            elif neg:
                sub_dag.apply_operation_back(XGate(), qargs=[q0])
                sub_dag.apply_operation_back(RZZGate(folded_theta), qargs=[q0, q1])
                sub_dag.apply_operation_back(XGate(), qargs=[q0])
            else:
                sub_dag.apply_operation_back(RZZGate(folded_theta), qargs=[q0, q1])

            dag.substitute_node_with_dag(node, sub_dag)

        return dag