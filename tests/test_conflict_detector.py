# -*- coding: utf-8 -*-
"""Unit tests for MitigationConflictDetector."""

from qiskit_neat_fold.conflict_detector import (
    MitigationConflictDetector,
    MitigationConflictError,
)


def test_conflict_fractional_and_gate_twirling():
    detector = MitigationConflictDetector(strict=True)
    options = {
        "use_fractional_gates": True,
        "twirling": {"enable_gates": True},
    }

    raised = False
    try:
        detector.inspect_options(options)
    except MitigationConflictError as e:
        raised = True
        assert "Mode A Violation" in str(e)
    assert raised, "Expected MitigationConflictError"


def test_conflict_fractional_and_pec():
    detector = MitigationConflictDetector(strict=True)
    options = {
        "use_fractional_gates": True,
        "resilience": {"pec_mitigation": True},
    }

    raised = False
    try:
        detector.inspect_options(options)
    except MitigationConflictError as e:
        raised = True
        assert "Mode A vs Mode B Clash" in str(e)
    assert raised, "Expected MitigationConflictError"


def test_conflict_trex_and_m3():
    detector = MitigationConflictDetector(strict=True)
    options = {
        "use_trex": True,
        "use_m3": True,
    }

    raised = False
    try:
        detector.inspect_options(options)
    except MitigationConflictError as e:
        raised = True
        assert "Measurement Mitigator Clash" in str(e)
    assert raised, "Expected MitigationConflictError"


def test_valid_mode_a_options():
    detector = MitigationConflictDetector(strict=True)
    options = {
        "use_fractional_gates": True,
        "twirling": {"enable_gates": False, "enable_measure": True}, # TREX is allowed in Mode A
        "use_m3": False,
        "resilience": {"pec_mitigation": False, "zne_mitigation": False},
    }

    conflicts = detector.inspect_options(options)
    assert len(conflicts) == 0
