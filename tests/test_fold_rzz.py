# -*- coding: utf-8 -*-
"""Unit tests for FoldRzzAnglePass and fold_angle_half_pi."""

import math
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator
from qiskit_neat_fold.fold_rzz import fold_angle_half_pi, FoldRzzAnglePass


def test_fold_angle_basic():
    # Angles already in (0, pi/2] should be preserved
    theta = 0.5
    f_theta, neg, refl, is_id = fold_angle_half_pi(theta)
    assert math.isclose(f_theta, 0.5, abs_tol=1e-10)
    assert not neg
    assert not refl
    assert not is_id

    # pi/2 boundary
    f_theta, neg, refl, is_id = fold_angle_half_pi(math.pi / 2.0)
    assert math.isclose(f_theta, math.pi / 2.0, abs_tol=1e-10)
    assert not neg
    assert not refl
    assert not is_id


def test_fold_angle_out_of_bounds():
    test_angles = [1.2, 2.5, 3.14159, -0.8, -2.2, 4.5, -5.0]
    for angle in test_angles:
        f_theta, neg, refl, is_id = fold_angle_half_pi(angle)
        assert 0.0 <= f_theta <= (math.pi / 2.0) + 1e-12, f"Failed for angle {angle}: got {f_theta}"


def test_fold_rzz_pass_unitary_equivalence():
    test_angles = [1.09956, 2.67035, -1.25664, 0.45, -2.5, 3.1415, -0.1, -3.0, 5.0, -5.0]
    
    for theta in test_angles:
        qc = QuantumCircuit(2)
        qc.rzz(theta, 0, 1)

        op_orig = Operator(qc)

        dag = circuit_to_dag(qc)
        pass_instance = FoldRzzAnglePass()
        folded_dag = pass_instance.run(dag)
        folded_qc = dag_to_circuit(folded_dag)

        op_folded = Operator(folded_qc)

        # Unitary equivalent up to global phase
        assert op_orig.equiv(op_folded), f"Unitary equivalence failed for theta={theta}"
