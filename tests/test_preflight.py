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
    assert res.depth == 4
    assert res.num_2q_gates == 3
    assert res.clifford_retention > 0.80
    assert res.estimated_ru_cost > 0.0
    assert len(res.warnings) == 0


def test_preflight_shot_warning():
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    preflight = NeatCliffordPreflight()
    res = preflight.evaluate(qc, shots=10000)

    # Should trigger shot inflation warning
    assert any("Shot budget warning" in w for w in res.warnings)


def test_preflight_deep_circuit():
    # Construct a circuit with excessive depth
    qc = QuantumCircuit(2)
    for _ in range(500):
        qc.cx(0, 1)

    preflight = NeatCliffordPreflight()
    res = preflight.evaluate(qc, shots=4096)

    # 500 CNOTs should drop Clifford retention significantly
    assert not res.is_viable
    assert any("Severe noise degradation" in w for w in res.warnings)
