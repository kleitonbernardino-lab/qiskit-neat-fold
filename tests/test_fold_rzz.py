# -*- coding: utf-8 -*-
"""Unit tests for FoldRzzAnglePass and fold_angle_half_pi."""

import math
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag, dag_to_circuit
from qiskit.quantum_info import Operator
from qiskit_neat_fold.fold_rzz import fold_angle_half_pi, FoldRzzAnglePass


def _max_phase_aligned_error(op_a: Operator, op_b: Operator) -> float:
    """Computes max elementwise error after aligning global phase."""
    mat_a = op_a.data
    mat_b = op_b.data
    idx = np.unravel_index(np.argmax(np.abs(mat_a)), mat_a.shape)
    if np.abs(mat_b[idx]) > 1e-15:
        phase = mat_a[idx] / mat_b[idx]
        phase = phase / np.abs(phase)
    else:
        phase = 1.0
    return float(np.max(np.abs(mat_a - phase * mat_b)))


def test_fold_angle_basic():
    f_theta, neg, refl, is_id = fold_angle_half_pi(0.5)
    assert math.isclose(f_theta, 0.5, abs_tol=1e-12)
    assert not neg and not refl and not is_id

    f_theta, neg, refl, is_id = fold_angle_half_pi(math.pi / 2.0)
    assert math.isclose(f_theta, math.pi / 2.0, abs_tol=1e-12)
    assert not neg and not refl and not is_id


def test_fold_angle_singular_pi_and_two_pi():
    for k in (-2, -1, 0, 1, 2):
        f_theta, neg, refl, is_id = fold_angle_half_pi(2.0 * k * math.pi)
        assert f_theta == 0.0 and is_id is True and refl is False

    for k in (-3, -1, 1, 3):
        f_theta, neg, refl, is_id = fold_angle_half_pi(k * math.pi)
        assert f_theta == 0.0 and is_id is False and refl is True


def test_fold_angle_near_pi_respects_strict_tol():
    # pi - 1e-9 must NOT collapse to +pi when tol=1e-12
    eps = 1e-9
    f_theta, neg, refl, is_id = fold_angle_half_pi(math.pi - eps, tol=1e-12)
    assert is_id is False
    assert refl is True
    assert math.isclose(f_theta, eps, rel_tol=1e-6, abs_tol=1e-15)

    # -pi + 1e-9 must also retain residual angle ~1e-9
    f_theta_neg, neg2, refl2, is_id2 = fold_angle_half_pi(-math.pi + eps, tol=1e-12)
    assert is_id2 is False
    assert neg2 is True and refl2 is True
    assert math.isclose(f_theta_neg, eps, rel_tol=1e-6, abs_tol=1e-15)


def test_fold_angle_invalid_inputs_and_tol():
    for bad in (float("nan"), float("inf"), float("-inf"), True, "1.0"):
        with pytest.raises(ValueError):
            fold_angle_half_pi(bad)  # type: ignore[arg-type]

    for bad_tol in (0.0, -1e-12, 1e-2, 0.5, float("nan"), True):
        with pytest.raises(ValueError):
            fold_angle_half_pi(0.5, tol=bad_tol)  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        FoldRzzAnglePass(target_tolerance=0.1)


def test_fold_rzz_pass_unitary_equivalence():
    eps = 1e-9
    test_angles = [
        0.0, 2.0 * math.pi, -2.0 * math.pi,
        math.pi, -math.pi, 3.0 * math.pi, -3.0 * math.pi,
        math.pi - eps, math.pi + eps, -math.pi - eps, -math.pi + eps,
        math.pi / 2.0, -math.pi / 2.0,
        1.09956, 2.67035, -1.25664, 0.45, -2.5, 5.0, -5.0,
    ]
    for theta in test_angles:
        qc = QuantumCircuit(2)
        qc.rzz(theta, 0, 1)
        op_orig = Operator(qc)
        folded_qc = dag_to_circuit(FoldRzzAnglePass(target_tolerance=1e-12).run(circuit_to_dag(qc)))
        op_folded = Operator(folded_qc)

        assert op_orig.equiv(op_folded), f"Unitary equivalence failed for theta={theta}"
        err = _max_phase_aligned_error(op_orig, op_folded)
        assert err < 1e-12, f"Matrix error {err} exceeded 1e-12 for theta={theta}"