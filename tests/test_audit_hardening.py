import os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
import pytest
from qiskit import QuantumCircuit
from qiskit_neat_fold.conflict_detector import MitigationConflictDetector, MitigationConflictError
from qiskit_neat_fold.preflight import NeatCliffordPreflight
from api.index import handle_api_request


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
    assert res_cliff.num_measured_qubits == 0

    qc_non = QuantumCircuit(2)
    qc_non.rzz(0.47124, 0, 1)
    qc_non.measure_all()
    res_non = pf.evaluate(qc_non)
    assert res_non.is_clifford is False
    assert res_non.num_measured_qubits == 2


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


def test_preflight_from_backend_rates_and_3plus_qubit_gates():
    pf = NeatCliffordPreflight.from_backend_rates(
        avg_1q_error=0.0002,
        avg_2q_error=0.0018,
        avg_readout_error=0.010,
        backend_name="ibm_kingston",
        timestamp_utc="2026-11-23T04:27:28Z",
        aggregation_method="median",
    )
    qc = QuantumCircuit(3)
    qc.ccx(0, 1, 2)  # 3-qubit Toffoli tracked separately in num_3plus_q_gates
    res = pf.evaluate(qc)
    assert res.calibration_source == "user_supplied:ibm_kingston@2026-11-23T04:27:28Z(median)"
    assert res.num_3plus_q_gates == 1
    assert res.num_2q_gates == 0
    assert any("Uncompiled multi-qubit gates" in w for w in res.warnings)


def test_api_endpoints_single_source_of_truth():
    status, data_fold = handle_api_request("/api/fold", {"theta": 3.141592653589793})
    assert status == 200
    assert data_fold["is_identity"] is False
    assert data_fold["is_odd_pi_zz"] is True

    status_pf, data_pf = handle_api_request(
        "/api/preflight",
        {"depth": 10, "num_1q": 20, "num_2q": 5, "num_measured_qubits": 3, "shots": 4096},
    )
    assert status_pf == 200
    assert data_pf["num_measured_qubits"] == 3
    assert data_pf["is_clifford"] is None

    status_cf, data_cf = handle_api_request(
        "/api/conflict",
        {"use_fractional_gates": True, "resilience_level": 2},
    )
    assert status_cf == 200
    assert data_cf["valid"] is True
    assert len(data_cf["warnings"]) == 1
def test_api_rejects_bool_float_and_missing_measured_qubits():
    st1, d1 = handle_api_request("/api/preflight", {"depth": 10, "num_1q": 5, "num_2q": 2})
    assert st1 == 400
    assert "num_measured_qubits" in d1["message"]

    st2, _ = handle_api_request("/api/preflight", {"num_measured_qubits": 2, "shots": True})
    assert st2 == 400
    st3, _ = handle_api_request("/api/preflight", {"num_measured_qubits": 2, "shots": 2.7})
    assert st3 == 400

    st4, _ = handle_api_request("/api/fold", {"theta": 1e9})
    assert st4 == 400
def test_boundary_32pi_and_alias_conflict():
    import math
    from qiskit import QuantumCircuit
    from qiskit.converters import circuit_to_dag, dag_to_circuit
    from qiskit.quantum_info import Operator
    from qiskit_neat_fold.fold_rzz import FoldRzzAnglePass
    from tests.test_fold_rzz import _max_phase_aligned_error

    # Near 32*pi boundary preserves precision < 1e-12
    theta_edge = (32.0 * math.pi) - 1e-9
    qc = QuantumCircuit(2)
    qc.rzz(theta_edge, 0, 1)
    folded = dag_to_circuit(FoldRzzAnglePass(target_tolerance=1e-12).run(circuit_to_dag(qc)))
    assert _max_phase_aligned_error(Operator(qc), Operator(folded)) < 1e-12

    # Beyond 32*pi is cleanly rejected (HTTP 400)
    st_over, _ = handle_api_request("/api/fold", {"theta": 33.0 * math.pi})
    assert st_over == 400

    # Conflicting num_measured_qubits vs num_meas alias -> HTTP 400
    st_alias, d_alias = handle_api_request(
        "/api/preflight",
        {"num_measured_qubits": 2, "num_meas": 4},
    )
    assert st_alias == 400
    assert "Conflicting" in d_alias["message"]
def test_wsgi_and_http_invalid_json_constants():
    import io
    from api.index import app, handler

    for bad_body in ('{"theta": NaN}', '{"theta": Infinity}', '{"theta": -Infinity}', '{"theta": '):
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = headers

        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": "/api/fold",
            "CONTENT_LENGTH": str(len(bad_body.encode("utf-8"))),
            "wsgi.input": io.BytesIO(bad_body.encode("utf-8")),
        }
        chunks = list(app(environ, start_response))
        assert captured["status"].startswith("400"), f"Expected 400 for {bad_body!r}, got {captured['status']}"
        assert len(chunks) == 1

    # Also verify BaseHTTPRequestHandler POST error path returns HTTP 400
    sent = {}

    class DummyHandler(handler):
        def __init__(self, body_str: str):
            self.path = "/api/fold"
            raw_bytes = body_str.encode("utf-8")
            self.headers = {"Content-Length": str(len(raw_bytes))}
            self.rfile = io.BytesIO(raw_bytes)
            self.wfile = io.BytesIO()
            self._status = None

        def send_response(self, code, message=None):
            self._status = code

        def send_header(self, keyword, value):
            sent.setdefault("headers", {})[keyword] = value

        def end_headers(self):
            pass

    dh = DummyHandler('{"theta": NaN}')
    dh.do_POST()
    assert dh._status == 400