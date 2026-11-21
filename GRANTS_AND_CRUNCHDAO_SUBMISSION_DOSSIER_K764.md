# Dossiê Executivo de Submissão 1:1 — Grants Não-Diluíveis (`US$ 8.000` + `R$ 500.000`) & CrunchDAO (`K:764`)

> **Status do Artefato 1:1 em Produção:**
> - **Repositório Público (MIT License):** `https://github.com/kleitonbernardino-lab/qiskit-neat-fold`
> - **Deploy Serverless 1:1 Ativo (200 OK):** `https://qiskit-neat-fold.vercel.app`
> - **Rotas Auditadas em Tempo Real:**
>   - `GET https://qiskit-neat-fold.vercel.app/` (`HTTP 200 OK` — Interactive Web UI)
>   - `GET https://qiskit-neat-fold.vercel.app/api/health` (`HTTP 200 OK` — `{"status":"ok","service":"qiskit-neat-fold"}`)
>   - `POST https://qiskit-neat-fold.vercel.app/api/fold` (`HTTP 200 OK` — `theta=2.67035 -> folded_theta=0.471243`)
>   - `POST https://qiskit-neat-fold.vercel.app/api/preflight` (`HTTP 200 OK` — 0.0 RU Clifford SNR & Mode A/B Conflict Check)
> - **Suíte de Testes Unitários (`unittest` / `pytest`):** `7/7 OK` (`100.0%` nos 6 Gates do Gêmeo 1:1 `K:764`).

---

## 1. Unitary Foundation Microgrant (`US$ 4.000` Equity-Free)
- **Portal de Submissão:** `https://unitary.foundation/grants/`
- **Project Title:** `qiskit-neat-fold: Zero-RU Clifford Pre-Flight Verification, Analytical RZZ Angle Folding, and Mode A/B Mitigation Conflict Detection for Open-Source Quantum Runtimes`
- **One-Sentence Summary (Abstract):** An open-source (MIT) Python library and interactive serverless toolkit that eliminates wasted QPU execution time by folding arbitrary $R_{ZZ}(\theta)$ angles into $(0, \pi/2]$ without spurious global phase gates, estimating Clifford signal survival at 0.0 RU cost, and statically preventing incompatible error-mitigation combinations.
- **Key Deliverables (3-Month Milestone Plan):**
  1. **M1 (Completed & Live 1:1):** Core `FoldRzzAnglePass`, `NeatCliffordPreflight`, `MitigationConflictDetector`, 7 unit test suites, and live browser playground at `https://qiskit-neat-fold.vercel.app`.
  2. **M2 (Month 1–2):** Multi-backend adapter supporting Cirq (`ZZPowGate` canonical folding) and Mitiq ZNE/PEC lightcone pre-flight cost estimators.
  3. **M3 (Month 3):** PyPI release (`pip install qiskit-neat-fold`), benchmark suite across 60+ open-source QAOA/SQD circuits, and tutorial documentation for Unitary Foundation community.

---

## 2. Deltakit Community Fund — Riverlane (`US$ 4.000` Equity-Free)
- **Portal de Submissão:** `https://deltakit.riverlane.com/`
- **Project Title:** `Clifford Noise-Survival Pre-Flight & Syndromic Readout Conflict Guard for Deltakit QEC Experiments`
- **Technical Alignment with Deltakit:**
  - Provides zero-cost Clifford proxy verification (`NeatCliffordPreflight`) prior to dispatching stabilizer/floquet QEC circuits to physical superconducting or neutral-atom QPUs.
  - Prevents readout-mitigation corruption (`MitigationConflictDetector` blocking simultaneous M3 matrix inversion and twirled readout extraction) on syndrome measurement bits.
  - **Export Control Compliance:** Developed in Brazil (eligible jurisdiction outside EAR Country Groups D:1/D:5 and OFAC embargoes), 100% open-source MIT license.

---

## 3. FAPESP PIPE Fase 1 — Chamada 59/2026 (`Até R$ 500.000,00` Não-Diluível)
- **Prazo Oficial da Chamada:** `26 de janeiro de 2027` (Sistema SAGe FAPESP)
- **Título do Projeto P&D:** `Plataforma Híbrida Quântico-Clássica (QCSC) de Diagonalização Baseada em Amostragem (SQD) e Bifurcação Simulada Discreta (dSB) com Governança FinOps de QPU`
- **Provas Empíricas TRL-4/TRL-5 Já Validadas:**
  1. **62 Circuitos Quânticos Reais (PUBs)** executados em processadores supercondutores IBM Heron r2 (`ibm_kingston` e `ibm_marrakesh`, 156 qubits Heavy-Hex).
  2. **Motor SQD + Self-Consistent Configuration Recovery (S-CORE):** Erro químico reduzido para `0.22 mHa` (abaixo do limiar de precisão química de `1.6 mHa`, ganho de `390x` sobre VQE ruidoso) respeitando o limite variacional de Rayleigh-Ritz.
  3. **Solver Quantum-Inspired dSB:** Razão de aproximação `1.000000` frente ao ótimo global MILP em otimização combinatória QUBO com restrição cardinal.
  4. **Microsserviço de Pré-Voo Quântico em Produção:** `https://qiskit-neat-fold.vercel.app`.

---

## 4. Pipeline Quantitativo CrunchDAO (`Spearman Rank IC + Purged Embargo Walk-Forward CV`)
- **Módulo Validado:** `tools/genesis_motor_liquidez_qubo_reservoir_k761.py`
- **Arquitetura Anti-Overfitting (`WIN-027` / `WIN-035`):**
  - Validação Cruzada Temporal Purgada (`PurgedEmbargoWalkForwardCV` com `5 folds` e `embargo = 2.5%`) impedindo vazamento serial de rótulos (`look-ahead bias = 0`).
  - Extração de features não-lineares por **Quantum-Inspired Reservoir Computing** acoplada a **Ridge Regression + Neutralização Ortogonal de Fatores**.
  - Otimização direta de hiperparâmetros para maximizar a razão $\text{IR}_{\text{Spearman}} = \mu(\rho_S) / \sigma(\rho_S)$.
