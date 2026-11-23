# -*- coding: utf-8 -*-
"""
fold_rzz.py: TransformationPass for analytical folding of RZZ angles to (0, pi/2].

Physical superconducting architectures with fixed-frequency transmons (e.g., IBM Heron r2)
calibrate native cross-resonance and ZZ interactions over the fundamental domain theta in (0, pi/2].
This pass folds arbitrary finite RZZ parameters analytically into (0, pi/2] using local
single-qubit Clifford conjugations (X, Z), preserving exact two-qubit unitary equivalence
up to global phase without introducing GlobalPhaseGate nodes.
"""

from __future__ import annotations
import math
from typing import Tuple
from qiskit.transpiler.basepasses import TransformationPass
from qiskit.dagcircuit import DAGCircuit
from qiskit.circuit.library import RZZGate, ZGate, XGate
from qiskit.circuit import ParameterExpression


def fold_angle_half_pi(theta: float, tol: float = 1e-12) -> Tuple[float, bool, bool, bool]:
    """
    Folds a finite angle theta in R into the fundamental calibration window (0, pi/2].

    Returns:
        (folded_theta, neg, reflected, is_identity)

    Mathematical identities (up to global phase):
        - RZZ(2*k*pi) = I (x) I -> (0.0, False, False, True)
        - RZZ((2*k+1)*pi) = -i (Z (x) Z) -> (0.0, False, True, False) [requires Z0 * Z1]
        - RZZ(-theta) = X0 * RZZ(theta) * X0
        - RZZ(pi - theta) = Z0 * Z1 * X0 * RZZ(theta) * X0
    """
    if isinstance(theta, bool) or not isinstance(theta, (int, float)) or not math.isfinite(theta):
        raise ValueError(f"Angle theta must be a finite real number, got {theta!r}")
    if tol <= 0 or not math.isfinite(tol):
        raise ValueError(f"Tolerance tol must be positive and finite, got {tol!r}")

    tau = 2.0 * math.pi
    # Wrap to (-pi, pi]
    norm_theta = ((theta + math.pi) % tau) - math.pi
    # Handle exact -pi boundary consistently as +pi
    if math.isclose(norm_theta, -math.pi, abs_tol=tol):
        norm_theta = math.pi

    # Multiple of 2*pi -> exact identity up to global phase
    if abs(norm_theta) < tol:
        return 0.0, False, False, True

    neg = False
    if norm_theta < 0.0:
        norm_theta = -norm_theta
        neg = True

    reflected = False
    if norm_theta > (math.pi / 2.0) + tol:
        norm_theta = math.pi - norm_theta
        reflected = True

    # Odd multiple of pi (norm_theta ~ pi after reflection -> 0.0 with reflected=True)
    if abs(norm_theta) < tol:
        return 0.0, False, True, False

    norm_theta = max(tol, min(math.pi / 2.0, norm_theta))
    return float(norm_theta), neg, reflected, False


class FoldRzzAnglePass(TransformationPass):
    """
    Transpiler transformation pass that folds all bound RZZGate parameters to (0, pi/2].
    """

    def __init__(self, target_tolerance: float = 1e-12):
        super().__init__()
        self.target_tolerance = target_tolerance

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

            folded_theta, neg, reflected, is_id = fold_angle_half_pi(
                theta_val, tol=self.target_tolerance
            )

            sub_dag = DAGCircuit()
            q0 = node.qargs[0]
            q1 = node.qargs[1]
            sub_dag.add_qubits([q0, q1])

            if is_id:
                # RZZ(2*k*pi) == I (x) I
                dag.substitute_node_with_dag(node, sub_dag)
                continue

            if reflected and folded_theta == 0.0:
                # RZZ((2*k+1)*pi) == -i (Z0 (x) Z1)
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
