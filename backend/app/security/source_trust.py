"""
source_trust.py

Determines how much the agent should trust a piece of evidence based on
WHERE it came from (its provenance) — never based on what the content
itself claims. This is the first line of defense: trust is a property
of the source, not something content can assert about itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceType(str, Enum):
    """Known provenance categories for evidence entering the agent."""

    INTERNAL_DATABASE = "internal_database"
    VERIFIED_TRANSACTION_RECORD = "verified_transaction_record"
    VERIFIED_CUSTOMER_RECORD = "verified_customer_record"
    MERCHANT_API = "merchant_api"
    EXTERNAL_WEBPAGE = "external_webpage"
    UPLOADED_DOCUMENT = "uploaded_document"
    UNKNOWN = "unknown"


class TrustLevel(str, Enum):
    """Coarse trust tiers assigned per source type."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"


# Fixed mapping of source -> trust tier. Deliberately static and
# provenance-based: nothing about the *content* of a piece of evidence
# can move its source up this table.
_SOURCE_TRUST_MAP: dict[SourceType, TrustLevel] = {
    SourceType.INTERNAL_DATABASE: TrustLevel.HIGH,
    SourceType.VERIFIED_TRANSACTION_RECORD: TrustLevel.HIGH,
    SourceType.VERIFIED_CUSTOMER_RECORD: TrustLevel.HIGH,
    SourceType.MERCHANT_API: TrustLevel.MEDIUM,
    SourceType.EXTERNAL_WEBPAGE: TrustLevel.LOW,
    SourceType.UPLOADED_DOCUMENT: TrustLevel.LOW,
    SourceType.UNKNOWN: TrustLevel.UNTRUSTED,
}

# Trust tiers considered strong enough, on their own, to support a
# sensitive action. Anything below this line needs corroboration.
_TRUSTED_LEVELS = {TrustLevel.HIGH, TrustLevel.MEDIUM}


@dataclass(frozen=True)
class SourceTrustResult:
    """Structured result of a source-trust lookup."""

    source: SourceType
    trust_level: TrustLevel
    trusted: bool
    reason: str


def classify_source(source: SourceType | str) -> SourceTrustResult:
    """
    Classify a piece of evidence's trust based purely on its source type.

    Args:
        source: A SourceType, or a raw string matched against known
            source types. Unrecognized strings are treated as
            SourceType.UNKNOWN (i.e. untrusted by default).

    Returns:
        SourceTrustResult describing the trust tier and whether the
        source is trusted enough to support sensitive decisions on its own.
    """
    if not isinstance(source, SourceType):
        try:
            source = SourceType(source)
        except ValueError:
            source = SourceType.UNKNOWN

    trust_level = _SOURCE_TRUST_MAP.get(source, TrustLevel.UNTRUSTED)
    trusted = trust_level in _TRUSTED_LEVELS

    reason = (
        f"Source '{source.value}' is classified as {trust_level.value} trust "
        f"based on provenance, not content."
    )

    return SourceTrustResult(
        source=source,
        trust_level=trust_level,
        trusted=trusted,
        reason=reason,
    )