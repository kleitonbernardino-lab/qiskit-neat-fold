# -*- coding: utf-8 -*-
"""Unit tests for NeatCliffordPreflight."""

from qiskit import QuantumCircuit
from qiskit_neat_fold.preflight import NeatCliffordPreflight


def test_preflight_small_circuit():
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.cx(2, 3)

    preflight = NeatCliffordPreflight()
    res = preflight.evaluate(qc, shots=4096)

    assert res.is_viable
    assert res.is_clifford
    assert res.depth == 4
    assert res.num_2q_gates == 3
    assert res.estimated_retention > 0.80
    assert len(res.warnings) == 0


def test_preflight_shot_warning():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    preflight = NeatCliffordPreflight()
    res = preflight.evaluate(qc, shots=16384)

    assert any("Shot budget warning" in w for w in res.warnings)


def test_preflight_deep_circuit():
    qc = QuantumCircuit(2)
    for _ in range(500):
        qc.cx(0, 1)

    preflight = NeatCliffordPreflight()
    res = preflight.evaluate(qc, shots=4096)

    assert not res.is_viable
    assert any("High attenuation warning" in w for w in res.warnings)
