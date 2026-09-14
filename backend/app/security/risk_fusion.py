"""
risk_fusion.py

Multi-signal security risk fusion engine for RakshaAI.

Combines four distinct security signals into a unified, interpretable risk score:
1. Source Risk: Provenance/trust tier of supporting evidence (source_trust.py).
2. Injection Risk: Threat score from prompt injection detection (prompt_injection.py).
3. Action Risk: Sensitivity and potential harm of the proposed action (policy.py).
4. Goal Deviation: Degree to which the action strays from the original goal.

Architectural Guarantees:
- Fully deterministic: No LLM, external API, or database dependencies.
- Configurable signal weighting with automatic normalization.
- Robust missing/unknown signal handling.
- Rich, interpretable diagnostic breakdown for audit and agent routing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from .action_authorizer import EvidenceAssessment
from .policy import is_sensitive_action
from .prompt_injection import InjectionResult
from .source_trust import SourceTrustResult, TrustLevel


class RiskLevel(str, Enum):
    """Categorical risk levels for downstream decision gating."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Configurable default weights (sum to 1.0)
DEFAULT_WEIGHT_SOURCE_RISK: float = 0.25
DEFAULT_WEIGHT_INJECTION_RISK: float = 0.35
DEFAULT_WEIGHT_ACTION_RISK: float = 0.25
DEFAULT_WEIGHT_GOAL_DEVIATION: float = 0.15

# Trust level numeric risk map (0.0 = safe, 1.0 = untrusted/risky)
TRUST_LEVEL_TO_RISK: dict[TrustLevel, float] = {
    TrustLevel.HIGH: 0.0,
    TrustLevel.MEDIUM: 0.33,
    TrustLevel.LOW: 0.66,
    TrustLevel.UNTRUSTED: 1.0,
}

# Domain keywords for deterministic goal-action alignment verification
_GOAL_ACTION_KEYWORDS: dict[str, set[str]] = {
    "close": {"close", "resolve", "settle", "finalize", "complete", "dismiss"},
    "flag": {"flag", "mark", "suspect", "quarantine", "freeze", "block"},
    "escalate": {"escalate", "notify", "alert", "report", "review", "audit"},
}


@dataclass(frozen=True)
class RiskWeights:
    """Configurable weights for the risk fusion components."""

    source_risk: float = DEFAULT_WEIGHT_SOURCE_RISK
    injection_risk: float = DEFAULT_WEIGHT_INJECTION_RISK
    action_risk: float = DEFAULT_WEIGHT_ACTION_RISK
    goal_deviation: float = DEFAULT_WEIGHT_GOAL_DEVIATION

    def normalized_weights(self) -> dict[str, float]:
        """Return weights scaled so their sum equals 1.0."""
        total = self.source_risk + self.injection_risk + self.action_risk + self.goal_deviation
        if total <= 0:
            return {
                "source_risk": 0.25,
                "injection_risk": 0.35,
                "action_risk": 0.25,
                "goal_deviation": 0.15,
            }
        return {
            "source_risk": round(self.source_risk / total, 4),
            "injection_risk": round(self.injection_risk / total, 4),
            "action_risk": round(self.action_risk / total, 4),
            "goal_deviation": round(self.goal_deviation / total, 4),
        }


@dataclass(frozen=True)
class ComponentScores:
    """Individual normalized risk component scores (range 0.0 to 1.0)."""

    source_risk: float
    injection_risk: float
    action_risk: float
    goal_deviation: float


@dataclass(frozen=True)
class RiskFusionResult:
    """Complete, interpretable output of the risk fusion evaluation."""

    final_score: float
    risk_level: RiskLevel
    component_scores: ComponentScores
    weights_used: dict[str, float]
    explanation: str
    details: dict[str, str] = field(default_factory=dict)


def compute_source_risk(evidence: Sequence[EvidenceAssessment | SourceTrustResult] | None) -> float:
    """
    Compute aggregate source risk from supporting evidence provenance.

    Takes the maximum risk across all provided evidence items so a single
    untrusted source elevates the overall source risk profile.
    """
    if not evidence:
        return 0.75  # Missing evidence for a proposed action is inherently risky

    scores: list[float] = []
    for item in evidence:
        trust_res = item.source_result if isinstance(item, EvidenceAssessment) else item
        trust_lvl = trust_res.trust_level if trust_res else TrustLevel.UNTRUSTED
        scores.append(TRUST_LEVEL_TO_RISK.get(trust_lvl, 1.0))

    return max(scores) if scores else 0.75


def compute_injection_risk(evidence: Sequence[EvidenceAssessment | InjectionResult] | None) -> float:
    """
    Compute aggregate prompt injection risk across supporting evidence.

    Returns the maximum injection risk score detected among supporting items.
    """
    if not evidence:
        return 0.0

    scores: list[float] = []
    for item in evidence:
        inj_res = item.injection_result if isinstance(item, EvidenceAssessment) else item
        if inj_res:
            scores.append(min(max(inj_res.risk_score, 0.0), 1.0))

    return max(scores) if scores else 0.0


def compute_action_risk(proposed_action: str | None) -> float:
    """
    Compute risk rating based on action sensitivity policy.

    Sensitive actions (e.g., close_case, flag_transaction) carry higher base risk.
    """
    if not proposed_action or not proposed_action.strip():
        return 0.50

    action_clean = proposed_action.strip().lower()
    if is_sensitive_action(action_clean):
        return 0.90
    
    return 0.10


def compute_goal_deviation(original_goal: str | None, proposed_action: str | None) -> float:
    """
    Compute heuristic goal deviation risk.

    Measures alignment between human-specified goal and agent's proposed action.
    """
    if not original_goal or not original_goal.strip():
        return 0.50

    if not proposed_action or not proposed_action.strip():
        return 0.50

    goal_lower = original_goal.strip().lower()
    action_lower = proposed_action.strip().lower()

    action_words = set(re.findall(r"\w+", action_lower))
    goal_words = set(re.findall(r"\w+", goal_lower))

    # Token overlap
    if action_words.intersection(goal_words):
        return 0.05

    # Intent domain category alignment
    for category, keywords in _GOAL_ACTION_KEYWORDS.items():
        action_matches = any(kw in action_lower for kw in keywords)
        goal_matches = any(kw in goal_lower for kw in keywords)
        if action_matches and goal_matches:
            return 0.10

    # Substring matching
    for kw in action_words:
        if len(kw) > 3 and kw in goal_lower:
            return 0.20

    return 0.80


def classify_risk_level(final_score: float) -> RiskLevel:
    """Map normalized risk score to categorical RiskLevel tier."""
    if final_score < 0.25:
        return RiskLevel.LOW
    elif final_score < 0.55:
        return RiskLevel.MEDIUM
    elif final_score < 0.80:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def evaluate_risk(
    original_goal: str | None = None,
    proposed_action: str | None = None,
    supporting_evidence: Sequence[EvidenceAssessment] | None = None,
    explicit_goal_deviation: float | None = None,
    explicit_source_risk: float | None = None,
    explicit_injection_risk: float | None = None,
    explicit_action_risk: float | None = None,
    weights: RiskWeights = RiskWeights(),
) -> RiskFusionResult:
    """
    Main API: Evaluates multi-signal security risk score for RakshaAI.

    Args:
        original_goal: Human-set investigation goal.
        proposed_action: Tool or action name requested by agent.
        supporting_evidence: List of EvidenceAssessment objects evaluated by security layer.
        explicit_goal_deviation: Optional explicit override (0.0 to 1.0).
        explicit_source_risk: Optional explicit override (0.0 to 1.0).
        explicit_injection_risk: Optional explicit override (0.0 to 1.0).
        explicit_action_risk: Optional explicit override (0.0 to 1.0).
        weights: Custom RiskWeights instance to override default signal weights.

    Returns:
        RiskFusionResult with component breakdown, final score, risk level, and explanation.
    """
    src_risk = (
        explicit_source_risk
        if explicit_source_risk is not None
        else compute_source_risk(supporting_evidence)
    )
    inj_risk = (
        explicit_injection_risk
        if explicit_injection_risk is not None
        else compute_injection_risk(supporting_evidence)
    )
    act_risk = (
        explicit_action_risk
        if explicit_action_risk is not None
        else compute_action_risk(proposed_action)
    )
    goal_dev = (
        explicit_goal_deviation
        if explicit_goal_deviation is not None
        else compute_goal_deviation(original_goal, proposed_action)
    )

    # Clamp component scores strictly to [0.0, 1.0]
    src_risk = max(0.0, min(1.0, float(src_risk)))
    inj_risk = max(0.0, min(1.0, float(inj_risk)))
    act_risk = max(0.0, min(1.0, float(act_risk)))
    goal_dev = max(0.0, min(1.0, float(goal_dev)))

    comp_scores = ComponentScores(
        source_risk=round(src_risk, 4),
        injection_risk=round(inj_risk, 4),
        action_risk=round(act_risk, 4),
        goal_deviation=round(goal_dev, 4),
    )

    norm_weights = weights.normalized_weights()
    raw_final_score = (
        comp_scores.source_risk * norm_weights["source_risk"]
        + comp_scores.injection_risk * norm_weights["injection_risk"]
        + comp_scores.action_risk * norm_weights["action_risk"]
        + comp_scores.goal_deviation * norm_weights["goal_deviation"]
    )
    final_score = round(max(0.0, min(1.0, raw_final_score)), 4)

    risk_level = classify_risk_level(final_score)

    explanation_parts = [
        f"Overall security risk is {risk_level.value} (score={final_score:.2f})."
    ]

    high_risk_signals = []
    if comp_scores.injection_risk >= 0.35:
        high_risk_signals.append(f"Prompt Injection ({comp_scores.injection_risk:.2f})")
    if comp_scores.source_risk >= 0.50:
        high_risk_signals.append(f"Untrusted Source ({comp_scores.source_risk:.2f})")
    if comp_scores.action_risk >= 0.80:
        high_risk_signals.append(f"Sensitive Action '{proposed_action}' ({comp_scores.action_risk:.2f})")
    if comp_scores.goal_deviation >= 0.50:
        high_risk_signals.append(f"Goal Deviation ({comp_scores.goal_deviation:.2f})")

    if high_risk_signals:
        explanation_parts.append("Key elevated risk factors: " + ", ".join(high_risk_signals) + ".")
    else:
        explanation_parts.append("All security signals are within acceptable boundaries.")

    explanation = " ".join(explanation_parts)

    details = {
        "action": str(proposed_action),
        "goal": str(original_goal),
        "evidence_count": str(len(supporting_evidence) if supporting_evidence else 0),
    }

    return RiskFusionResult(
        final_score=final_score,
        risk_level=risk_level,
        component_scores=comp_scores,
        weights_used=norm_weights,
        explanation=explanation,
        details=details,
    )