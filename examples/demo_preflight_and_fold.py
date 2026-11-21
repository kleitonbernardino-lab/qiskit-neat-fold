# -*- coding: utf-8 -*-
"""
demo_preflight_and_fold.py: Example demonstrating FoldRzzAnglePass and NeatCliffordPreflight.
"""

import math
from qiskit import QuantumCircuit
from qiskit.transpiler import PassManager
from qiskit_neat_fold import (
    FoldRzzAnglePass,
    NeatCliffordPreflight,
    MitigationConflictDetector,
)


def main():
    print("=== QISKIT-NEAT-FOLD END-TO-END DEMO ===")

    # 1. Create a circuit with out-of-bounds fractional angles
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    # RZZ with angles exceeding pi/2 or negative
    qc.rzz(2.67035, 1, 2)
    qc.rzz(-1.25664, 2, 3)
    qc.rzz(1.09956, 0, 3)

    print("\n1. Original Circuit:")
    print(qc.draw(output="text"))

    # 2. Run Pre-flight Clifford Verification (0.0 RU)
    preflight = NeatCliffordPreflight()
    result = preflight.evaluate(qc, shots=4096)

    print("\n2. Zero-RU Pre-flight Verification:")
    print(f"   - Viable: {result.is_viable}")
    print(f"   - Estimated Clifford Retention: {result.clifford_retention:.2%}")
    print(f"   - Circuit Depth: {result.depth}")
    print(f"   - 2Q Gates: {result.num_2q_gates}")
    print(f"   - Estimated RU Cost: {result.estimated_ru_cost:.5f} RU (~{result.estimated_duration_sec:.2f} s)")

    # 3. Transpile with FoldRzzAnglePass
    pm = PassManager([FoldRzzAnglePass()])
    folded_qc = pm.run(qc)

    print("\n3. Transpiled Circuit (All RZZ Angles Folded to (0, pi/2]):")
    print(folded_qc.draw(output="text"))

    # 4. Check Runtime Mitigation Options for Incompatibilities
    detector = MitigationConflictDetector(strict=False)
    options_sample = {
        "use_fractional_gates": True,
        "twirling": {"enable_gates": False, "enable_measure": True}, # Mode A compliant
        "use_m3": False,
    }
    conflicts = detector.inspect_options(options_sample)
    print("\n4. Mitigation Conflict Detection:")
    if not conflicts:
        print("   [OK] Options are fully compliant with Mode A (Fractional Gates + DD/TREX).")
    else:
        for c in conflicts:
            print(f"   [WARN] {c}")

    print("\n=== DEMO COMPLETED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
