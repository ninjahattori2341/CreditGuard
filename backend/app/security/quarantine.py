"""
quarantine.py

Suspicious evidence is never silently dropped. It is quarantined: kept
available for audit and human review, but explicitly marked as
non-authoritative so it cannot influence agent decisions unless a human
deliberately releases it.

IMPORTANT: Quarantined evidence must never automatically become trusted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .prompt_injection import InjectionResult
from .source_trust import SourceTrustResult


@dataclass
class QuarantineRecord:
    """A quarantined (or cleared) piece of evidence, kept for audit purposes."""

    evidence_id: str
    original_evidence: str
    source_result: SourceTrustResult
    injection_result: InjectionResult
    quarantined: bool
    reason: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    released: bool = False
    release_reason: str | None = None


# In-memory store for hackathon-demo purposes. A real deployment would
# back this with persistent storage (DB/table), but the interface below
# would stay the same.
_QUARANTINE_STORE: dict[str, QuarantineRecord] = {}


def quarantine_evidence(
    evidence_id: str,
    original_evidence: str,
    source_result: SourceTrustResult,
    injection_result: InjectionResult,
) -> QuarantineRecord:
    """
    Evaluate and (if warranted) quarantine a piece of evidence.

    Evidence is quarantined if its source is untrusted OR prompt
    injection was detected in it. The evidence text itself is always
    preserved for audit — only its authority to influence decisions
    is revoked.
    """
    should_quarantine = (not source_result.trusted) or injection_result.is_injection

    reasons = []
    if not source_result.trusted:
        reasons.append(f"untrusted source ({source_result.trust_level.value})")
    if injection_result.is_injection:
        reasons.append(f"prompt injection detected (risk={injection_result.risk_score})")

    reason = (
        "Quarantined: " + "; ".join(reasons)
        if should_quarantine
        else "Not quarantined: source trusted and no injection detected."
    )

    record = QuarantineRecord(
        evidence_id=evidence_id,
        original_evidence=original_evidence,
        source_result=source_result,
        injection_result=injection_result,
        quarantined=should_quarantine,
        reason=reason,
    )

    _QUARANTINE_STORE[evidence_id] = record
    return record


def is_quarantined(evidence_id: str) -> bool:
    """Check whether a given evidence id is currently quarantined and unreleased."""
    record = _QUARANTINE_STORE.get(evidence_id)
    return bool(record and record.quarantined and not record.released)


def release_evidence(evidence_id: str, release_reason: str) -> QuarantineRecord | None:
    """
    Explicitly release evidence from quarantine after human review.

    This requires an explicit, human-supplied reason and is always
    logged on the record. Release does NOT upgrade the evidence's
    underlying source trust level or re-run injection detection — it
    only unblocks the record from being treated as quarantined, and
    the fact that it was originally flagged remains on the audit trail.
    """
    record = _QUARANTINE_STORE.get(evidence_id)
    if record is None:
        return None

    record.released = True
    record.release_reason = release_reason
    return record


def get_quarantine_record(evidence_id: str) -> QuarantineRecord | None:
    """Retrieve the quarantine record for a given evidence id, if any."""
    return _QUARANTINE_STORE.get(evidence_id)