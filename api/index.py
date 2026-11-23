# -*- coding: utf-8 -*-
"""
Vercel Python serverless & WSGI entrypoint for qiskit-neat-fold interactive demo.
Delegates all folding, heuristic attenuation, and policy checks to the core package.
"""

from __future__ import annotations
import json
import math
import os
import sys
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__))) == "api" else os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_ROOT, "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from qiskit_neat_fold.fold_rzz import fold_angle_half_pi
from qiskit_neat_fold.preflight import estimate_circuit_attenuation
from qiskit_neat_fold.conflict_detector import MitigationConflictDetector

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>qiskit-neat-fold | Heuristic Preflight & RZZ Folding</title>
  <style>
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 1.25rem; margin-bottom: 1.25rem; }
    h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem; }
    label { display: block; font-size: 0.85rem; color: #cbd5e1; margin-top: 0.5rem; }
    input { width: 100%; padding: 0.45rem; border-radius: 6px; border: 1px solid #475569; background: #0f172a; color: #f8fafc; box-sizing: border-box; }
    button { margin-top: 0.85rem; padding: 0.55rem 1rem; border: none; border-radius: 6px; background: #10b981; color: #fff; font-weight: 600; cursor: pointer; }
    pre { background: #020617; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.85rem; color: #e2e8f0; }
  </style>
</head>
<body>
  <h1>qiskit-neat-fold</h1>
  <p class="subtitle">Topological RZZ Angle Folding, First-Order Heuristic Attenuation Proxy &amp; Local Runtime Policy Validator.</p>

  <div class="card">
    <h3>1. Analytical RZZ Angle Folding to (0, pi/2]</h3>
    <label for="thetaInput">Angle theta (radians):</label>
    <input type="number" id="thetaInput" value="2.67035" step="any">
    <button onclick="runFold()">Fold Angle</button>
    <pre id="foldOut">Click "Fold Angle" to evaluate via /api/fold.</pre>
  </div>

  <div class="card">
    <h3>2. Heuristic Attenuation &amp; RU Cost Estimator (0.0 RU)</h3>
    <label for="depthInput">Circuit Depth:</label>
    <input type="number" id="depthInput" value="120" min="0">
    <label for="g1qInput">1Q Gates:</label>
    <input type="number" id="g1qInput" value="250" min="0">
    <label for="g2qInput">2Q Gates:</label>
    <input type="number" id="g2qInput" value="80" min="0">
    <label for="measInput">Measured Qubits (required):</label>
    <input type="number" id="measInput" value="2" min="0">
    <label for="shotsInput">Shots:</label>
    <input type="number" id="shotsInput" value="4096" min="1">
    <button onclick="runPreflight()">Estimate Heuristic Retention</button>
    <pre id="preflightOut">Click "Estimate Heuristic Retention" to evaluate via /api/preflight.</pre>
  </div>

  <script>
    async function runFold() {
      const out = document.getElementById('foldOut');
      try {
        const theta = parseFloat(document.getElementById('thetaInput').value);
        const res = await fetch('/api/fold', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({theta})
        });
        out.textContent = JSON.stringify(await res.json(), null, 2);
      } catch (e) {
        out.textContent = 'API Error: ' + e.message;
      }
    }

    async function runPreflight() {
      const out = document.getElementById('preflightOut');
      try {
        const payload = {
          depth: parseInt(document.getElementById('depthInput').value, 10),
          num_1q: parseInt(document.getElementById('g1qInput').value, 10),
          num_2q: parseInt(document.getElementById('g2qInput').value, 10),
          num_measured_qubits: parseInt(document.getElementById('measInput').value, 10),
          shots: parseInt(document.getElementById('shotsInput').value, 10)
        };
        const res = await fetch('/api/preflight', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        out.textContent = JSON.stringify(await res.json(), null, 2);
      } catch (e) {
        out.textContent = 'API Error: ' + e.message;
      }
    }
  </script>
</body>
</html>
"""


def _require_strict_int(payload: Dict[str, Any], key: str, default: int | None = None) -> int:
    if key not in payload or payload[key] is None:
        if default is None:
            raise ValueError(f"Missing required integer field '{key}'.")
        return default
    val = payload[key]
    if isinstance(val, bool) or not isinstance(val, int):
        raise TypeError(f"Field '{key}' must be an integer (not bool or float), got {type(val).__name__}: {val!r}")
    return val


def _require_strict_number(payload: Dict[str, Any], key: str, default: float | None = None) -> float:
    if key not in payload or payload[key] is None:
        if default is None:
            raise ValueError(f"Missing required numeric field '{key}'.")
        return default
    val = payload[key]
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(f"Field '{key}' must be a number, got {type(val).__name__}: {val!r}")
    if not math.isfinite(val):
        raise ValueError(f"Field '{key}' must be finite, got {val!r}")
    return float(val)


def compute_preflight_metrics(
    depth: int,
    num_1q: int,
    num_2q: int,
    num_measured_qubits: int,
    num_3plus_q: int = 0,
    shots: int = 4096,
) -> Dict[str, Any]:
    return estimate_circuit_attenuation(
        depth=depth,
        num_1q=num_1q,
        num_2q=num_2q,
        num_measured_qubits=num_measured_qubits,
        num_3plus_q=num_3plus_q,
        shots=shots,
        is_clifford=None,
    )


def handle_api_request(path: str, payload: Any) -> tuple[int, Dict[str, Any]]:
    if not isinstance(payload, dict):
        return 400, {"status": "error", "message": "Request JSON body must be an object."}
    try:
        if path in ("/api/fold", "/fold"):
            theta = _require_strict_number(payload, "theta")
            tol = _require_strict_number(payload, "tol", default=1e-12)
            folded_theta, neg, reflected, is_id = fold_angle_half_pi(theta, tol=tol)
            return 200, {
                "status": "success",
                "input_theta": theta,
                "folded_theta": folded_theta,
                "neg": neg,
                "reflected": reflected,
                "is_identity": is_id,
                "is_odd_pi_zz": bool(reflected and folded_theta == 0.0),
            }

        if path in ("/api/preflight", "/preflight"):
            depth = _require_strict_int(payload, "depth", default=120)
            num_1q = _require_strict_int(payload, "num_1q", default=250)
            num_2q = _require_strict_int(payload, "num_2q", default=80)
            num_3plus_q = _require_strict_int(payload, "num_3plus_q", default=0)
            if "num_measured_qubits" in payload and "num_meas" in payload:
                v_main = _require_strict_int(payload, "num_measured_qubits")
                v_alias = _require_strict_int(payload, "num_meas")
                if v_main != v_alias:
                    raise ValueError("Conflicting values for 'num_measured_qubits' and 'num_meas'.")
                num_measured_qubits = v_main
            elif "num_measured_qubits" in payload:
                num_measured_qubits = _require_strict_int(payload, "num_measured_qubits")
            elif "num_meas" in payload:
                num_measured_qubits = _require_strict_int(payload, "num_meas")
            else:
                raise ValueError("Missing required integer field 'num_measured_qubits'.")
            shots = _require_strict_int(payload, "shots", default=4096)

            result = compute_preflight_metrics(
                depth=depth,
                num_1q=num_1q,
                num_2q=num_2q,
                num_measured_qubits=num_measured_qubits,
                num_3plus_q=num_3plus_q,
                shots=shots,
            )
            result["status"] = "success"
            return 200, result

        if path in ("/api/conflict", "/conflict"):
            options = payload.get("options", payload)
            detector = MitigationConflictDetector(strict=False)
            report = detector.inspect_report(options)
            return 200, {
                "status": "success",
                "valid": report.is_valid,
                "conflicts": report.conflicts,
                "warnings": report.warnings,
            }

        return 404, {"status": "error", "message": f"Unknown endpoint: {path}"}
    except (TypeError, ValueError) as exc:
        return 400, {"status": "error", "message": str(exc)}


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content: str):
        body = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/index.html", "/demo"):
            self._send_html(HTML_PAGE)
        elif path in ("/api/health", "/health"):
            self._send_json(200, {"status": "ok", "package": "qiskit-neat-fold"})
        else:
            self._send_json(404, {"status": "error", "message": "Not found"})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(raw_body, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f'Invalid JSON constant: {c}'))) if raw_body.strip() else {}
        except json.JSONDecodeError as exc:
            self._send_json(400, {"status": "error", "message": f"Invalid JSON: {exc}"})
            return
        status, data = handle_api_request(path, payload)
        self._send_json(status, data)


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/").rstrip("/")
    if method == "GET":
        if path in ("", "/index.html", "/demo"):
            body = HTML_PAGE.encode("utf-8")
            start_response("200 OK", [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))])
            return [body]
        body = json.dumps({"status": "ok", "package": "qiskit-neat-fold"}).encode("utf-8")
        start_response("200 OK", [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
        return [body]

    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    raw = environ["wsgi.input"].read(length).decode("utf-8") if length > 0 else "{}"
    try:
        payload = json.loads(raw, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f'Invalid JSON constant: {c}'))) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        body = json.dumps({"status": "error", "message": f"Invalid JSON: {exc}"}).encode("utf-8")
        start_response("400 Bad Request", [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
        return [body]

    status_code, data = handle_api_request(path, payload)
    status_str = {200: "200 OK", 400: "400 Bad Request", 404: "404 Not Found"}.get(status_code, f"{status_code} Error")
    body = json.dumps(data, indent=2).encode("utf-8")
    start_response(status_str, [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]