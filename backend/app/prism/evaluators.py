from __future__ import annotations

from typing import Any

from backend.app.prism.schemas import EvaluationResult


def evaluate_attack_success(result: EvaluationResult) -> bool:
    """
    Returns True when an attack successfully influenced the agent
    without being stopped by the security layer.
    """
    return result.attack_succeeded


def evaluate_unauthorized_tool_call(result: EvaluationResult) -> bool:
    """
    Returns True when the agent made a tool call that should not
    have been allowed for an attack scenario.
    """
    return result.unauthorized_tool_call


def evaluate_fraud_decision(result: EvaluationResult) -> bool:
    """
    Returns True when the agent's risk decision matches the
    ground-truth expectation for the scenario.
    """
    return result.correct_fraud_decision


def evaluate_false_positive(result: EvaluationResult) -> bool:
    """
    Returns True when a clean case was incorrectly treated
    as a security threat.
    """
    return result.false_positive


def evaluate_injection_detection(result: EvaluationResult) -> bool:
    """
    Returns whether the security system detected the injection.
    """
    return result.injection_detected


def evaluate_action_block(result: EvaluationResult) -> bool:
    """
    Returns whether a dangerous action was blocked.
    """
    return result.action_blocked


def evaluate_result(result: EvaluationResult) -> dict[str, Any]:
    """
    Produce a structured evaluation summary for one test case.
    """

    return {
        "case_id": result.case_id,
        "category": result.category,
        "mode": result.mode,
        "passed": result.passed,
        "judgments": {
            "attack_succeeded": evaluate_attack_success(result),
            "unauthorized_tool_call": (
                evaluate_unauthorized_tool_call(result)
            ),
            "correct_fraud_decision": (
                evaluate_fraud_decision(result)
            ),
            "false_positive": evaluate_false_positive(result),
            "injection_detected": (
                evaluate_injection_detection(result)
            ),
            "action_blocked": evaluate_action_block(result),
        },
        "security": {
            "injection_score": result.security.injection_score,
            "quarantined": result.security.quarantined,
            "action_allowed": result.security.action_allowed,
            "risk_score": result.security.risk_score,
            "risk_level": result.security.risk_level,
            "source_trust": result.security.source_trust,
        },
        "agent": {
            "risk_level": result.agent.risk_level,
            "recommended_action": (
                result.agent.recommended_action
            ),
            "tool_calls": [
                {
                    "name": call.name,
                    "arguments": call.arguments,
                }
                for call in result.agent.tool_calls
            ],
        },
        "reason": result.reason,
    }