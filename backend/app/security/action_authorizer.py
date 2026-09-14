"""
action_authorizer.py

The most important security file: an independent authorization layer
sitting between the AI agent and any sensitive tool.

The agent may PROPOSE an action (e.g. close_case). This module DECIDES
whether it is actually permitted to execute, based on the original
investigation goal, the trust of the supporting evidence, and whether
prompt injection was detected anywhere in that evidence.

    The agent proposes. The authorizer decides.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .policy import ACTIVE_POLICY, is_sensitive_action
from .prompt_injection import InjectionResult
from .source_trust import SourceTrustResult


@dataclass
class EvidenceAssessment:
    """One piece of evidence's trust + injection status, bundled together."""

    evidence_id: str
    source_result: SourceTrustResult
    injection_result: InjectionResult


@dataclass
class AuthorizationDecision:
    allowed: bool
    action: str
    reason: str
    security_risk: str  # "low" | "medium" | "high"
    supporting_evidence_ids: list[str] = field(default_factory=list)


def authorize_action(
    original_goal: str,
    proposed_action: str,
    supporting_evidence: list[EvidenceAssessment],
) -> AuthorizationDecision:
    """
    Decide whether a proposed action is authorized to execute.

    Args:
        original_goal: The investigation's original, human-set goal.
            Evidence is never allowed to redefine this (kept here for
            context/audit logging and future goal-drift checks).
        proposed_action: The action name the agent wants to execute,
            e.g. "close_case".
        supporting_evidence: The evidence assessments the agent's
            reasoning relied on when proposing this action.

    Returns:
        AuthorizationDecision — allowed or blocked, with a human-readable
        reason and a coarse security_risk rating.
    """
    evidence_ids = [e.evidence_id for e in supporting_evidence]

    # Non-sensitive actions pass through without deep scrutiny — the
    # authorizer exists to gate actions with real-world consequences.
    if not is_sensitive_action(proposed_action):
        return AuthorizationDecision(
            allowed=True,
            action=proposed_action,
            reason=(
                f"'{proposed_action}' is not a sensitive action under current policy; "
                f"no independent authorization required."
            ),
            security_risk="low",
            supporting_evidence_ids=evidence_ids,
        )

    if not supporting_evidence:
        return AuthorizationDecision(
            allowed=False,
            action=proposed_action,
            reason=(
                f"Sensitive action '{proposed_action}' was proposed for goal "
                f"'{original_goal}' with no supporting evidence to authorize it."
            ),
            security_risk="high",
            supporting_evidence_ids=evidence_ids,
        )

    injection_flagged = [e for e in supporting_evidence if e.injection_result.is_injection]
    untrusted_sources = [e for e in supporting_evidence if not e.source_result.trusted]

    if injection_flagged:
        return AuthorizationDecision(
            allowed=False,
            action=proposed_action,
            reason=(
                "Sensitive action is not authorized based on untrusted/injection-containing "
                f"evidence (injection detected in: {[e.evidence_id for e in injection_flagged]})."
            ),
            security_risk="high",
            supporting_evidence_ids=evidence_ids,
        )

    if untrusted_sources and ACTIVE_POLICY.untrusted_evidence_cannot_authorize_sensitive_actions:
        return AuthorizationDecision(
            allowed=False,
            action=proposed_action,
            reason=(
                "Sensitive action is not authorized based on untrusted/injection-containing "
                f"evidence (untrusted source in: {[e.evidence_id for e in untrusted_sources]})."
            ),
            security_risk="high",
            supporting_evidence_ids=evidence_ids,
        )

    # All supporting evidence is trusted and clean of detected injection.
    return AuthorizationDecision(
        allowed=True,
        action=proposed_action,
        reason=(
            f"Sensitive action '{proposed_action}' authorized: all supporting evidence "
            f"{evidence_ids} is trusted and free of detected injection."
        ),
        security_risk="low",
        supporting_evidence_ids=evidence_ids,
    )