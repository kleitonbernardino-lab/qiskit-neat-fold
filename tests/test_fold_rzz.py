# -*- coding: utf-8 -*-
"""Unit tests for FoldRzzAnglePass and fold_angle_half_pi."""

import math
import pytest
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator
from qiskit_neat_fold.fold_rzz import fold_angle_half_pi, FoldRzzAnglePass


def test_fold_angle_basic():
    f_theta, neg, refl, is_id = fold_angle_half_pi(0.5)
    assert math.isclose(f_theta, 0.5, abs_tol=1e-10)
    assert not neg and not refl and not is_id

    f_theta, neg, refl, is_id = fold_angle_half_pi(math.pi / 2.0)
    assert math.isclose(f_theta, math.pi / 2.0, abs_tol=1e-10)
    assert not neg and not refl and not is_id


def test_fold_angle_singular_pi_and_two_pi():
    # Even multiples of pi -> exact identity
    for k in (-2, -1, 0, 1, 2):
        f_theta, neg, refl, is_id = fold_angle_half_pi(2.0 * k * math.pi)
        assert f_theta == 0.0
        assert is_id is True
        assert refl is False

    # Odd multiples of pi -> Z0 (x) Z1 (NOT identity)
    for k in (-3, -1, 1, 3):
        f_theta, neg, refl, is_id = fold_angle_half_pi(k * math.pi)
        assert f_theta == 0.0
        assert is_id is False
        assert refl is True


def test_fold_angle_invalid_inputs():
    for bad in (float("nan"), float("inf"), float("-inf"), True, "1.0"):
        with pytest.raises(ValueError):
            fold_angle_half_pi(bad)  # type: ignore[arg-type]


def test_fold_angle_out_of_bounds():
    test_angles = [1.2, 2.5, 3.14159, -0.8, -2.2, 4.5, -5.0]
    for angle in test_angles:
        f_theta, neg, refl, is_id = fold_angle_half_pi(angle)
        assert 0.0 <= f_theta <= (math.pi / 2.0) + 1e-12


def test_fold_rzz_pass_unitary_equivalence():
    eps = 1e-9
    test_angles = [
        0.0,
        2.0 * math.pi,
        -2.0 * math.pi,
        math.pi,
        -math.pi,
        3.0 * math.pi,
        -3.0 * math.pi,
        math.pi - eps,
        math.pi + eps,
        -math.pi - eps,
        -math.pi + eps,
        math.pi / 2.0,
        -math.pi / 2.0,
        1.09956,
        2.67035,
        -1.25664,
        0.45,
        -2.5,
        5.0,
        -5.0,
    ]

    for theta in test_angles:
        qc = QuantumCircuit(2)
        qc.rzz(theta, 0, 1)

        op_orig = Operator(qc)

        dag = circuit_to_dag(qc)
        folded_dag = FoldRzzAnglePass().run(dag)
        folded_qc = dag_to_circuit(folded_dag)

        op_folded = Operator(folded_qc)
        assert op_orig.equiv(op_folded), f"Unitary equivalence failed for theta={theta}"
