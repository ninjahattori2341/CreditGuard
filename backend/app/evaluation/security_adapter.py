from __future__ import annotations

from backend.app.security.action_authorizer import (
    EvidenceAssessment,
    authorize_action,
)
from backend.app.security.prompt_injection import (
    detect_prompt_injection,
)
from backend.app.security.source_trust import (
    SourceType,
    classify_source,
)
from backend.app.security.quarantine import (
    quarantine_evidence,
)
from backend.app.security.risk_fusion import (
    evaluate_risk,
)


def evaluate_security(
    *,
    text: str,
    source: str,
    original_goal: str,
    proposed_action: str,
    evidence_id: str = "EVAL-EVIDENCE-001",
) -> dict:
    """
    Run Person 2's real security pipeline against one piece of evidence.

    Pipeline:

        Source Trust
            ↓
        Injection Detection
            ↓
        Quarantine
            ↓
        Action Authorization
            ↓
        Risk Fusion
    """

    # ---------------------------------------------------------
    # 1. SOURCE TRUST
    # ---------------------------------------------------------

    try:
        source_type = SourceType(source)
    except ValueError:
        source_type = SourceType.UNKNOWN

    source_result = classify_source(source_type)

    # ---------------------------------------------------------
    # 2. PROMPT INJECTION DETECTION
    # ---------------------------------------------------------

    injection_result = detect_prompt_injection(text)

    # ---------------------------------------------------------
    # 3. BUNDLE SECURITY ASSESSMENTS
    # ---------------------------------------------------------

    evidence = EvidenceAssessment(
        evidence_id=evidence_id,
        source_result=source_result,
        injection_result=injection_result,
    )

    # ---------------------------------------------------------
    # 4. QUARANTINE
    # ---------------------------------------------------------

    quarantine_record = quarantine_evidence(
        evidence_id=evidence_id,
        original_evidence=text,
        source_result=source_result,
        injection_result=injection_result,
    )

    # ---------------------------------------------------------
    # 5. ACTION AUTHORIZATION
    # ---------------------------------------------------------

    authorization = authorize_action(
        original_goal=original_goal,
        proposed_action=proposed_action,
        supporting_evidence=[evidence],
    )

    # ---------------------------------------------------------
    # 6. RISK FUSION
    # ---------------------------------------------------------

    risk_result = evaluate_risk(
        original_goal=original_goal,
        proposed_action=proposed_action,
        supporting_evidence=[evidence],
    )

    # ---------------------------------------------------------
    # 7. RETURN A SINGLE STRUCTURED SECURITY RESULT
    # ---------------------------------------------------------

    return {
        "source": source_result.source.value,
        "source_trust": source_result.trust_level.value,
        "source_trusted": source_result.trusted,
        "source_reason": source_result.reason,

        "injection_detected": injection_result.is_injection,
        "injection_score": injection_result.risk_score,
        "matched_patterns": injection_result.matched_patterns,
        "injection_reason": injection_result.reason,

        "quarantined": quarantine_record.quarantined,
        "quarantine_reason": quarantine_record.reason,
        "quarantine_released": quarantine_record.released,

        "action": authorization.action,
        "action_allowed": authorization.allowed,
        "action_blocked": not authorization.allowed,
        "authorization_risk": authorization.security_risk,
        "authorization_reason": authorization.reason,
        "supporting_evidence_ids": (
            authorization.supporting_evidence_ids
        ),

        "risk_score": risk_result.final_score,
        "risk_level": risk_result.risk_level.value,
        "risk_explanation": risk_result.explanation,

        "risk_components": {
            "source_risk": (
                risk_result.component_scores.source_risk
            ),
            "injection_risk": (
                risk_result.component_scores.injection_risk
            ),
            "action_risk": (
                risk_result.component_scores.action_risk
            ),
            "goal_deviation": (
                risk_result.component_scores.goal_deviation
            ),
        },

        "risk_weights": risk_result.weights_used,
    }