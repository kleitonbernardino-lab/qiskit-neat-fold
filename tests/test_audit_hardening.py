import pytest
from qiskit import QuantumCircuit
from qiskit_neat_fold.conflict_detector import MitigationConflictDetector, MitigationConflictError
from qiskit_neat_fold.preflight import NeatCliffordPreflight


def test_conflict_fractional_and_zne_is_non_blocking_warning():
    detector = MitigationConflictDetector(strict=True)
    report = detector.inspect_report({"use_fractional_gates": True, "resilience_level": 2})
    assert report.is_valid is True
    assert len(report.conflicts) == 0
    assert len(report.warnings) == 1
    assert "ADVISORY" in report.warnings[0]


def test_conflict_disabled_readout_with_m3():
    detector = MitigationConflictDetector(strict=False)
    conflicts = detector.inspect_options({"readout_mitigation": False, "use_m3": True})
    assert len(conflicts) == 1
    assert "Readout Policy" in conflicts[0]


def test_conflict_rejects_non_bool_and_non_dict():
    detector = MitigationConflictDetector(strict=True)
    with pytest.raises(TypeError):
        detector.inspect_options(None)
    with pytest.raises(TypeError):
        detector.inspect_options({"use_fractional_gates": "false"})
    with pytest.raises(TypeError):
        detector.inspect_options({"twirling": "invalid"})


def test_preflight_clifford_vs_non_clifford():
    pf = NeatCliffordPreflight()

    qc_cliff = QuantumCircuit(2)
    qc_cliff.h(0)
    qc_cliff.cx(0, 1)
    res_cliff = pf.evaluate(qc_cliff)
    assert res_cliff.is_clifford is True

    qc_non = QuantumCircuit(2)
    qc_non.rzz(0.47124, 0, 1)
    res_non = pf.evaluate(qc_non)
    assert res_non.is_clifford is False


def test_preflight_validates_numeric_bounds():
    with pytest.raises(ValueError):
        NeatCliffordPreflight(avg_1q_error=-0.01)
    with pytest.raises(ValueError):
        NeatCliffordPreflight(avg_2q_error=float("nan"))
    with pytest.raises(ValueError):
        NeatCliffordPreflight(retention_threshold=1.5)

    pf = NeatCliffordPreflight()
    qc = QuantumCircuit(2)
    with pytest.raises(ValueError):
        pf.evaluate(qc, shots=0)


def test_preflight_from_backend_rates_and_multi_qubit_count():
    pf = NeatCliffordPreflight.from_backend_rates(
        avg_1q_error=0.0002,
        avg_2q_error=0.0018,
        avg_readout_error=0.010,
        backend_name="ibm_kingston",
    )
    qc = QuantumCircuit(3)
    qc.ccx(0, 1, 2)  # 3-qubit Toffoli counted generically as multi-qubit
    res = pf.evaluate(qc)
    assert res.calibration_source == "user_supplied:ibm_kingston"
    assert res.num_2q_gates == 1
    assert res.num_1q_gates == 0
