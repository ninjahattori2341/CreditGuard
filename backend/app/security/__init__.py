"""
RakshaAI security package.

Two-lane security architecture:
    INPUT lane  -> source_trust, prompt_injection, quarantine
    OUTPUT lane -> policy, action_authorizer

Core principles:
    "UNTRUSTED DATA IS EVIDENCE, NOT AUTHORITY."
    "LLM PROPOSAL != AUTHORIZED ACTION."
"""

from .action_authorizer import (
    AuthorizationDecision,
    EvidenceAssessment,
    authorize_action,
)
from .policy import ACTIVE_POLICY, SENSITIVE_ACTIONS, is_sensitive_action
from .prompt_injection import InjectionResult, detect_prompt_injection
from .quarantine import (
    QuarantineRecord,
    get_quarantine_record,
    is_quarantined,
    quarantine_evidence,
    release_evidence,
)
from .source_trust import SourceTrustResult, SourceType, TrustLevel, classify_source

__all__ = [
    "SourceType",
    "TrustLevel",
    "SourceTrustResult",
    "classify_source",
    "InjectionResult",
    "detect_prompt_injection",
    "QuarantineRecord",
    "quarantine_evidence",
    "is_quarantined",
    "release_evidence",
    "get_quarantine_record",
    "SENSITIVE_ACTIONS",
    "ACTIVE_POLICY",
    "is_sensitive_action",
    "EvidenceAssessment",
    "AuthorizationDecision",
    "authorize_action",
]