# -*- coding: utf-8 -*-
"""
fold_rzz.py: TransformationPass for analytical folding of RZZ angles to (0, pi/2].

Physical superconducting architectures with fixed-frequency transmons (e.g., IBM Heron r2)
calibrate native cross-resonance and ZZ interactions over the fundamental domain theta in (0, pi/2].
Angles outside this range frequently trigger transpiler de-optimizations, excessive CX synthesis,
or runtime dispatch warnings. This pass folds RZZ parameters analytically into the calibration window.
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
    Folds an angle theta in R into the native calibration window (0, pi/2].

    Returns:
        (folded_theta, neg, reflected, is_identity)
        
    Mathematical relation:
        RZZ(theta) = exp(-i * theta/2 * Z (x) Z)
        Periodic in 2*pi.
        RZZ(-theta) = X0 * RZZ(theta) * X0
        RZZ(pi - theta) = Z0 * Z1 * X0 * RZZ(theta) * X0 [up to global phase]
    """
    tau = 2.0 * math.pi
    norm_theta = ((theta + math.pi) % tau) - math.pi

    if abs(norm_theta) < tol:
        return 0.0, False, False, True

    neg = False
    if norm_theta < 0:
        norm_theta = -norm_theta
        neg = True

    reflected = False
    if norm_theta > (math.pi / 2.0) + tol:
        norm_theta = math.pi - norm_theta
        reflected = True

    if abs(norm_theta) < tol:
        return 0.0, False, False, True

    norm_theta = max(tol, min(math.pi / 2.0, norm_theta))
    return float(norm_theta), neg, reflected, False


class FoldRzzAnglePass(TransformationPass):
    """
    Transpiler transformation pass that folds all RZZGate parameters to (0, pi/2].
    
    Inserts localized single-qubit corrections (X, Z) to guarantee exact unitary equivalence
    up to a global phase, without introducing spurious GlobalPhaseGate nodes.
    """

    def __init__(self, target_tolerance: float = 1e-12):
        super().__init__()
        self.target_tolerance = target_tolerance

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """
        Execute the transformation pass on DAGCircuit.
        """
        for node in dag.op_nodes():
            if node.op.name == "rzz":
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
                    dag.substitute_node_with_dag(node, sub_dag)
                    continue

                # Case analysis for exact unitary equivalence:
                if neg and reflected:
                    # X0 * (Z0 Z1 X0 RZZ X0) * X0 = - Z0 Z1 RZZ
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
