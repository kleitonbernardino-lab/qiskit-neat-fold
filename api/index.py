# -*- coding: utf-8 -*-
"""
api/index.py: Serverless Web Entrypoint and Interactive Verification Engine for Vercel.
Exposes interactive live UI and REST API endpoints for qiskit-neat-fold.
"""

from __future__ import annotations
import os
import sys
import json
import math
from http.server import BaseHTTPRequestHandler

# Add ../src to sys.path for local cleanroom package resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from qiskit_neat_fold.fold_rzz import fold_angle_half_pi
    from qiskit_neat_fold.conflict_detector import MitigationConflictDetector
except ImportError:
    # Pure Python zero-dependency fallback for lightning-fast serverless cold start
    def fold_angle_half_pi(theta: float, tol: float = 1e-12):
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

    class MitigationConflictDetector:
        def __init__(self, strict: bool = False):
            self.strict = strict
        def inspect_options(self, options: dict) -> list[str]:
            conflicts = []
            if options.get("use_fractional_gates") and options.get("twirling", {}).get("enable_gates"):
                conflicts.append("[Mode A Conflict] 'use_fractional_gates=True' cannot be combined with gate twirling.")
            if options.get("use_fractional_gates") and (options.get("resilience", {}).get("pec_mitigation") or options.get("resilience_level") == 3):
                conflicts.append("[Mode A Conflict] Fractional gates cannot be combined with PEC.")
            return conflicts


def compute_preflight_metrics(depth: int, num_1q: int, num_2q: int, num_meas: int = 2, shots: int = 4096):
    avg_1q_error = 0.0003
    avg_2q_error = 0.0025
    avg_readout_error = 0.015
    ru_rate_per_sec = 1.0 / 60.0

    retention_1q = (1.0 - avg_1q_error) ** max(0, num_1q)
    retention_2q = (1.0 - avg_2q_error) ** max(0, num_2q)
    retention_meas = (1.0 - avg_readout_error) ** max(0, num_meas)
    clifford_retention = float(retention_1q * retention_2q * retention_meas)

    est_duration_sec = float((depth * 350e-9 + 2.5e-6) * shots)
    est_ru_cost = float(est_duration_sec * ru_rate_per_sec)
    is_viable = clifford_retention >= 0.40

    warnings = []
    recommendations = []
    if not is_viable:
        warnings.append(f"Clifford retention ({clifford_retention:.1%}) is below 40% threshold. Circuit fidelity will collapse into depolarizing noise.")
        recommendations.append("Apply FoldRzzAnglePass and reduce circuit depth before hardware submission.")
    else:
        recommendations.append("Circuit passes preflight verification. Safe for zero-waste submission to IBM Quantum Runtime V2.")

    return {
        "is_viable": is_viable,
        "clifford_retention": round(clifford_retention, 4),
        "clifford_retention_percent": f"{clifford_retention * 100:.2f}%",
        "depth": depth,
        "num_1q_gates": num_1q,
        "num_2q_gates": num_2q,
        "estimated_duration_sec": round(est_duration_sec, 3),
        "estimated_ru_cost": round(est_ru_cost, 4),
        "warnings": warnings,
        "recommendations": recommendations,
    }


HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Qiskit Neat Fold — IBM Quantum Runtime V2 Optimizer</title>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚛️</text></svg>">
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(18, 26, 43, 0.85);
      --border: #233554;
      --accent-cyan: #00f2fe;
      --accent-emerald: #10b981;
      --accent-violet: #8b5cf6;
      --accent-rose: #f43f5e;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); min-height: 100vh; padding: 2rem 1rem; }
    .container { max-width: 1080px; margin: 0 auto; }
    header { text-align: center; margin-bottom: 2.5rem; }
    .badge { display: inline-block; padding: 0.35rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; letter-spacing: 0.05em; background: rgba(0, 242, 254, 0.15); color: var(--accent-cyan); border: 1px solid rgba(0, 242, 254, 0.3); margin-bottom: 0.75rem; text-transform: uppercase; }
    h1 { font-size: 2.4rem; font-weight: 800; background: linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.5rem; }
    .subtitle { color: var(--text-muted); font-size: 1.05rem; max-width: 720px; margin: 0 auto; line-height: 1.5; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; backdrop-filter: blur(12px); box-shadow: 0 10px 25px rgba(0,0,0,0.4); }
    .card-title { font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
    label { display: block; font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-bottom: 0.4rem; }
    input[type="number"], input[type="text"], select { width: 100%; padding: 0.7rem; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; color: #fff; font-size: 0.95rem; margin-bottom: 1rem; }
    input:focus, select:focus { outline: none; border-color: var(--accent-cyan); box-shadow: 0 0 10px rgba(0,242,254,0.25); }
    .btn { display: inline-flex; justify-content: center; align-items: center; width: 100%; padding: 0.75rem; border: none; border-radius: 8px; font-size: 0.95rem; font-weight: 700; cursor: pointer; transition: all 0.2s ease; background: linear-gradient(135deg, #00f2fe, #4facfe); color: #090d16; }
    .btn:hover { transform: translateY(-2px); box-shadow: 0 6px 18px rgba(0, 242, 254, 0.4); }
    .presets { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 1rem; }
    .preset-btn { background: #1e293b; border: 1px solid var(--border); color: var(--text); padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.75rem; cursor: pointer; transition: background 0.2s; }
    .preset-btn:hover { background: #334155; color: var(--accent-cyan); }
    .result-box { margin-top: 1rem; padding: 1rem; background: #0c1220; border: 1px solid var(--border); border-radius: 8px; font-size: 0.88rem; }
    .result-row { display: flex; justify-content: space-between; padding: 0.35rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
    .result-row:last-child { border-bottom: none; }
    .val-highlight { font-weight: 700; color: var(--accent-emerald); }
    .val-warn { font-weight: 700; color: var(--accent-rose); }
    .code-preview { background: #050811; padding: 0.75rem; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: 0.8rem; color: #a5f3fc; overflow-x: auto; margin-top: 0.5rem; border: 1px solid rgba(0,242,254,0.15); }
    footer { text-align: center; color: var(--text-muted); font-size: 0.85rem; padding-top: 2rem; border-top: 1px solid var(--border); }
    footer a { color: var(--accent-cyan); text-decoration: none; }
    footer a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">Open Source • Unitary Fund Ready</div>
      <h1>qiskit-neat-fold</h1>
      <p class="subtitle">
        Topological RZZ Angle Folding & 0.0-RU Preflight Verification Engine for IBM Quantum Runtime V2 (Heron r2 Heavy-Hex Architecture).
      </p>
    </header>

    <div class="grid">
      <!-- Tool 1: RZZ Angle Folding -->
      <div class="card">
        <div class="card-title">📐 RZZ Angle Folding</div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
          Folds unconstrained rotation angles θ ∈ ℝ into the hardware calibration window (0, π/2] with exact single-qubit Clifford corrections.
        </p>
        <label for="thetaInput">Rotation Angle θ (radians):</label>
        <input type="number" id="thetaInput" step="any" value="2.67035">
        <div class="presets">
          <span style="font-size:0.75rem; color:var(--text-muted); align-self:center;">Presets:</span>
          <button class="preset-btn" onclick="setTheta(2.67035)">2.67035</button>
          <button class="preset-btn" onclick="setTheta(-2.5)">-2.5</button>
          <button class="preset-btn" onclick="setTheta(2.356194)">3π/4</button>
          <button class="preset-btn" onclick="setTheta(-1.047198)">-π/3</button>
          <button class="preset-btn" onclick="setTheta(3.141593)">π</button>
        </div>
        <button class="btn" onclick="runFold()">⚡ Fold Angle Instantly</button>

        <div id="foldResult" class="result-box" style="display:none;">
          <div class="result-row"><span>Original Angle:</span> <strong id="resOrig">2.67035 rad</strong></div>
          <div class="result-row"><span>Folded Angle θ':</span> <strong class="val-highlight" id="resFolded">0.47124 rad</strong></div>
          <div class="result-row"><span>Calibration Domain:</span> <strong class="val-highlight">θ' ∈ (0, π/2]</strong></div>
          <div class="result-row"><span>Reflection (π - θ):</span> <span id="resReflected">True</span></div>
          <div class="result-row"><span>Negation (-θ):</span> <span id="resNeg">False</span></div>
          <div style="margin-top:0.75rem; font-size:0.8rem; color:var(--text-muted);">Injected Unitary Sequence:</div>
          <div class="code-preview" id="resSequence">Z(q0) • Z(q1) • X(q0) • RZZ(0.47124) • X(q0)</div>
        </div>
      </div>

      <!-- Tool 2: Preflight Clifford Signal Estimator -->
      <div class="card">
        <div class="card-title">🛡️ 0.0-RU Preflight Estimator</div>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
          Computes Clifford signal retention & hardware cost BEFORE execution, completely preventing wasted Quantum Runtime Seconds (RUs).
        </p>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem;">
          <div>
            <label for="depthInput">Circuit Depth:</label>
            <input type="number" id="depthInput" value="120" min="1">
          </div>
          <div>
            <label for="shotsInput">Total Shots:</label>
            <input type="number" id="shotsInput" value="4096" min="100">
          </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem;">
          <div>
            <label for="g1qInput">1Q Gates Count:</label>
            <input type="number" id="g1qInput" value="250" min="0">
          </div>
          <div>
            <label for="g2qInput">2Q Gates (CZ/ECR):</label>
            <input type="number" id="g2qInput" value="80" min="0">
          </div>
        </div>
        <button class="btn" onclick="runPreflight()" style="background: linear-gradient(135deg, #10b981, #059669); color:#fff;">
          🔍 Calculate Preflight Signal
        </button>

        <div id="preflightResult" class="result-box" style="display:none;">
          <div class="result-row"><span>Viability Status:</span> <strong id="resViable" class="val-highlight">VIABLE (PASS)</strong></div>
          <div class="result-row"><span>Clifford Retention:</span> <strong id="resRetention" class="val-highlight">81.8%</strong></div>
          <div class="result-row"><span>Est. QPU Duration:</span> <strong id="resDuration">0.182 s</strong></div>
          <div class="result-row"><span>Est. Cost (RUs):</span> <strong id="resRu">0.0030 RU</strong></div>
          <div class="code-preview" id="resPreflightMsg">Safe for zero-waste submission to IBM Quantum Runtime V2.</div>
        </div>
      </div>
    </div>

    <!-- Tool 3: Error Mitigation Incompatibility Detector -->
    <div class="card" style="margin-bottom: 2rem;">
      <div class="card-title">⚠️ Mitigation Incompatibility Auditor (Mode A vs Mode B)</div>
      <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
        IBM Quantum Runtime V2 enforces strict separation between Mode A (fractional gates) and Mode B (twirling + PEC/ZNE). Test options below:
      </p>
      <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-bottom: 1rem;">
        <label><input type="checkbox" id="chkFractional" checked onchange="auditMitigation()"> Native Fractional Gates</label>
        <label><input type="checkbox" id="chkTwirling" onchange="auditMitigation()"> Gate Pauli Twirling</label>
        <label><input type="checkbox" id="chkPEC" onchange="auditMitigation()"> Probabilistic Error Canc. (PEC)</label>
        <label><input type="checkbox" id="chkM3" checked onchange="auditMitigation()"> M3 Readout Mitigation</label>
      </div>
      <div class="result-box" id="mitigationAuditBox">
        <strong style="color:var(--accent-emerald);">✅ Mode A Compliant</strong>: Fractional Gates + Readout Mitigation without Clifford Twirling distortion.
      </div>
    </div>

    <footer>
      <p>
        <strong>qiskit-neat-fold v0.1.0</strong> • Clean-Room Engineered for Unitary Fund Microgrant & IBM Quantum Runtime V2.<br>
        Published on GitHub: <a href="https://github.com/kleitonbernardino-lab/qiskit-neat-fold" target="_blank">kleitonbernardino-lab/qiskit-neat-fold</a> • MIT Licensed.
      </p>
    </footer>
  </div>

  <script>
    function setTheta(val) {
      document.getElementById('thetaInput').value = val;
      runFold();
    }

    async function runFold() {
      const theta = parseFloat(document.getElementById('thetaInput').value);
      try {
        const res = await fetch('/api/fold', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({theta})
        });
        const data = await res.json();
        document.getElementById('resOrig').innerText = data.original_theta + ' rad';
        document.getElementById('resFolded').innerText = data.folded_theta + ' rad';
        document.getElementById('resReflected').innerText = data.reflected ? 'True (π - θ)' : 'False';
        document.getElementById('resNeg').innerText = data.neg ? 'True (-θ)' : 'False';
        document.getElementById('resSequence').innerText = data.clifford_sequence;
        document.getElementById('foldResult').style.display = 'block';
      } catch (e) {
        // Local calculation fallback
        const pi = Math.PI;
        const tau = 2.0 * pi;
        let norm = ((theta + pi) % tau) - pi;
        let neg = norm < 0;
        if (neg) norm = -norm;
        let reflected = norm > (pi / 2.0) + 1e-12;
        if (reflected) norm = pi - norm;
        norm = Math.max(1e-12, Math.min(pi / 2.0, norm));
        
        let seq = 'RZZ(' + norm.toFixed(5) + ')';
        if (neg && reflected) seq = 'Z(q0) • Z(q1) • RZZ(' + norm.toFixed(5) + ')';
        else if (reflected) seq = 'Z(q0) • Z(q1) • X(q0) • RZZ(' + norm.toFixed(5) + ') • X(q0)';
        else if (neg) seq = 'X(q0) • RZZ(' + norm.toFixed(5) + ') • X(q0)';

        document.getElementById('resOrig').innerText = theta.toFixed(5) + ' rad';
        document.getElementById('resFolded').innerText = norm.toFixed(5) + ' rad';
        document.getElementById('resReflected').innerText = reflected ? 'True (π - θ)' : 'False';
        document.getElementById('resNeg').innerText = neg ? 'True (-θ)' : 'False';
        document.getElementById('resSequence').innerText = seq;
        document.getElementById('foldResult').style.display = 'block';
      }
    }

    async function runPreflight() {
      const depth = parseInt(document.getElementById('depthInput').value) || 120;
      const shots = parseInt(document.getElementById('shotsInput').value) || 4096;
      const num_1q = parseInt(document.getElementById('g1qInput').value) || 250;
      const num_2q = parseInt(document.getElementById('g2qInput').value) || 80;

      try {
        const res = await fetch('/api/preflight', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({depth, shots, num_1q, num_2q})
        });
        const data = await res.json();
        renderPreflight(data);
      } catch (e) {
        // Local fallback calculation
        const ret1q = Math.pow(1.0 - 0.0003, num_1q);
        const ret2q = Math.pow(1.0 - 0.0025, num_2q);
        const ret = ret1q * ret2q * Math.pow(1.0 - 0.015, 2);
        const dur = (depth * 350e-9 + 2.5e-6) * shots;
        const ru = dur / 60.0;
        renderPreflight({
          is_viable: ret >= 0.40,
          clifford_retention_percent: (ret * 100).toFixed(2) + '%',
          estimated_duration_sec: dur.toFixed(3),
          estimated_ru_cost: ru.toFixed(4),
          recommendations: ret >= 0.40 ? ['Safe for zero-waste submission to IBM Quantum Runtime V2.'] : ['Clifford retention is below 40%. Circuit will collapse into depolarizing noise.']
        });
      }
    }

    function renderPreflight(data) {
      const elViable = document.getElementById('resViable');
      if (data.is_viable) {
        elViable.innerText = 'VIABLE (PASS)';
        elViable.className = 'val-highlight';
      } else {
        elViable.innerText = 'ABORT (FAIL)';
        elViable.className = 'val-warn';
      }
      document.getElementById('resRetention').innerText = data.clifford_retention_percent;
      document.getElementById('resDuration').innerText = data.estimated_duration_sec + ' s';
      document.getElementById('resRu').innerText = data.estimated_ru_cost + ' RU';
      document.getElementById('resPreflightMsg').innerText = (data.recommendations || []).join(' ');
      document.getElementById('preflightResult').style.display = 'block';
    }

    function auditMitigation() {
      const frac = document.getElementById('chkFractional').checked;
      const twirl = document.getElementById('chkTwirling').checked;
      const pec = document.getElementById('chkPEC').checked;
      const box = document.getElementById('mitigationAuditBox');

      if (frac && twirl) {
        box.innerHTML = '<strong style="color:var(--accent-rose);">❌ Conflict Detected (Mode A Violation)</strong>: Fractional gates cannot be twirled. Gate twirling projects rotations onto Clifford generators, destroying continuous angle calibration.';
      } else if (frac && pec) {
        box.innerHTML = '<strong style="color:var(--accent-rose);">❌ Conflict Detected (Mode A Violation)</strong>: PEC requires Pauli basis expansion and is mathematically incompatible with native continuous fractional cross-resonance.';
      } else if (frac) {
        box.innerHTML = '<strong style="color:var(--accent-emerald);">✅ Mode A Compliant</strong>: Fractional Gates + M3/TREX Readout Mitigation. Max QPU signal retention.';
      } else if (twirl || pec) {
        box.innerHTML = '<strong style="color:#38bdf8;">ℹ️ Mode B Compliant</strong>: Standard Clifford/CZ basis with Twirling and Active Noise Mitigation.';
      } else {
        box.innerHTML = '<span style="color:var(--text-muted);">Baseline unmitigated standard circuit.</span>';
      }
    }

    // Auto-run on load
    runFold();
    runPreflight();
  </script>
</body>
</html>
"""


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function Handler."""

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_content: str):
        body = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")
        if path in ("", "/index.html", "/demo"):
            self._send_html(HTML_UI)
        elif path == "/api/health":
            self._send_json(200, {
                "status": "ok",
                "package": "qiskit-neat-fold",
                "version": "0.1.0",
                "architecture": "IBM Quantum Heron r2 (Heavy-Hex)",
                "license": "MIT",
                "repository": "https://github.com/kleitonbernardino-lab/qiskit-neat-fold"
            })
        else:
            # Fallback to main UI for any non-API GET request
            self._send_html(HTML_UI)

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception as e:
            self._send_json(400, {"error": "Invalid JSON", "details": str(e)})
            return

        if path in ("/api/fold", "/fold"):
            theta = float(payload.get("theta", 2.67035))
            tol = float(payload.get("tol", 1e-12))
            folded_theta, neg, reflected, is_id = fold_angle_half_pi(theta, tol=tol)

            if is_id:
                sequence = "Identity (No gates)"
            elif neg and reflected:
                sequence = f"Z(q0) • Z(q1) • RZZ({folded_theta:.5f})"
            elif reflected:
                sequence = f"Z(q0) • Z(q1) • X(q0) • RZZ({folded_theta:.5f}) • X(q0)"
            elif neg:
                sequence = f"X(q0) • RZZ({folded_theta:.5f}) • X(q0)"
            else:
                sequence = f"RZZ({folded_theta:.5f})"

            self._send_json(200, {
                "status": "success",
                "original_theta": theta,
                "folded_theta": round(folded_theta, 6),
                "neg": neg,
                "reflected": reflected,
                "is_identity": is_id,
                "clifford_sequence": sequence,
                "domain": "(0, pi/2]",
                "target_hardware": "IBM Heron r2"
            })

        elif path in ("/api/preflight", "/preflight"):
            depth = int(payload.get("depth", 120))
            num_1q = int(payload.get("num_1q", 250))
            num_2q = int(payload.get("num_2q", 80))
            num_meas = int(payload.get("num_meas", 2))
            shots = int(payload.get("shots", 4096))

            result = compute_preflight_metrics(depth, num_1q, num_2q, num_meas, shots)
            result["status"] = "success"
            self._send_json(200, result)

        elif path in ("/api/conflict", "/conflict"):
            options = payload.get("options", payload)
            detector = MitigationConflictDetector(strict=False)
            conflicts = detector.inspect_options(options)
            self._send_json(200, {
                "status": "success",
                "valid": len(conflicts) == 0,
                "conflicts": conflicts
            })

        else:
            self._send_json(404, {"error": "Endpoint not found", "path": path})


if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(("0.0.0.0", 8080), handler)
    print("Serving qiskit-neat-fold demo at http://localhost:8080")
    server.serve_forever()
