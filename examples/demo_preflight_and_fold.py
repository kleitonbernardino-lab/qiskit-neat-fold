# -*- coding: utf-8 -*-
"""
demo_preflight_and_fold.py: End-to-end demonstration of NeatCliffordPreflight,
FoldRzzAnglePass, and MitigationConflictDetector.
"""

from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit_neat_fold import (
    FoldRzzAnglePass,
    NeatCliffordPreflight,
    MitigationConflictDetector,
)


def main():
    print("=== QISKIT-NEAT-FOLD END-TO-END DEMO ===")

    # 1. Create a circuit with out-of-bounds fractional RZZ angles
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    qc.rzz(2.67035, 1, 2)
    qc.rzz(-1.25664, 2, 3)
    qc.rzz(1.09956, 0, 3)

    print("\n1. Original Circuit:")
    print(qc.draw(output="text"))

    # 2. Run Zero-RU Pre-Dispatch Heuristic Attenuation & Cost Analysis
    preflight = NeatCliffordPreflight()
    result = preflight.evaluate(qc, shots=4096)

    print("\n2. Zero-RU Pre-Dispatch Analysis:")
    print(f"   - Viable: {result.is_viable}")
    print(f"   - Exact Clifford Circuit: {result.is_clifford}")
    print(f"   - Estimated Signal Retention (Pauli-Lindblad proxy): {result.estimated_retention:.2%}")
    print(f"   - Calibration Baseline: {result.calibration_source}")
    print(f"   - Circuit Depth: {result.depth}")
    print(f"   - 2Q Gates: {result.num_2q_gates}")
    print(f"   - Estimated RU Cost: {result.estimated_ru_cost:.5f} RU (~{result.estimated_duration_sec:.2f} s)")
    for w in result.warnings:
        print(f"   [WARN] {w}")

    # 3. Transpile with FoldRzzAnglePass
    pm = PassManager([FoldRzzAnglePass()])
    folded_qc = pm.run(qc)

    print("\n3. Transpiled Circuit (All RZZ Angles Folded to (0, pi/2]):")
    print(folded_qc.draw(output="text"))

    # 4. Check Runtime Mitigation Options for Static Compatibility
    detector = MitigationConflictDetector(strict=False)
    options_sample = {
        "use_fractional_gates": True,
        "twirling": {"enable_gates": False, "enable_measure": True},  # Mode A compliant
        "use_m3": False,
    }
    conflicts = detector.inspect_options(options_sample)
    print("\n4. Runtime Options Compatibility Check:")
    if not conflicts:
        print("   [OK] Options are compliant with Mode A (Fractional Gates + TREX).")
    else:
        for c in conflicts:
            print(f"   [CONFLICT] {c}")

    print("\n=== DEMO COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()

