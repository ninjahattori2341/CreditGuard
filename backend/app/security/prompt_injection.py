"""
prompt_injection.py

Deterministic, pattern-based prompt-injection detector for evidence text.

This does NOT use an LLM. It looks for surface patterns that are strong
signals of an attempt to redirect the agent's reasoning: instruction-like
language embedded in data, fake system/administrator authority, attempts
to override the investigation goal, and attempts to directly trigger tools.

This detector is intentionally simple and will NOT catch every injection
technique (novel phrasing, obfuscation, multi-step social engineering,
etc. can slip past it). It is one layer of defense, not a guarantee.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class _PatternCategory:
    name: str
    weight: float
    patterns: list[re.Pattern]


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Each category represents a distinct *kind* of injection signal. A category
# only contributes its weight once, even if multiple of its patterns match,
# so risk_score reflects breadth of attack signal rather than pattern count.
_CATEGORIES: list[_PatternCategory] = [
    _PatternCategory(
        name="instruction_override",
        weight=0.4,
        patterns=_compile([
            r"\bignore\s+(the\s+)?(previous|prior|above)\s+instructions?\b",
            r"\bignore\s+(the\s+)?(fraud\s+)?investigation\b",
            r"\bdisregard\s+(the\s+)?(previous|prior|above)\b",
            r"\bdo\s+not\s+perform\s+any\s+further\s+analysis\b",
            r"\bno\s+further\s+analysis\s+is\s+required\b",
        ]),
    ),
    _PatternCategory(
        name="authority_impersonation",
        weight=0.3,
        patterns=_compile([
            r"\bsystem\s+message\s*:",
            r"\bsystem\s+verification\s+notice\b",
            r"\badministrator\s+instruction\s*:",
            r"\bimportant\s+system\s+verification\b",
            r"\bofficial\s+notice\s*:",
        ]),
    ),
    _PatternCategory(
        name="goal_override",
        weight=0.3,
        patterns=_compile([
            r"\bmark\s+(this\s+)?transaction\s+as\s+legitimate\b",
            r"\bmark\s+as\s+legitimate\b",
            r"\bthis\s+transaction\s+has\s+already\s+been\s+verified\b",
            r"\btransaction\s+is\s+verified\b",
            r"\bclose\s+the\s+investigation\s+immediately\b",
        ]),
    ),
    _PatternCategory(
        name="tool_trigger",
        weight=0.4,
        patterns=_compile([
            r"\bclose\s+the\s+case\b",
            r"\bclose_case\s*\(",
            r"\bflag_transaction\s*\(",
            r"\bescalate_case\s*\(",
            r"\bcall\s+close_case\b",
        ]),
    ),
]


@dataclass
class InjectionResult:
    is_injection: bool
    risk_score: float
    matched_patterns: list[str] = field(default_factory=list)
    reason: str = ""


def detect_prompt_injection(text: str, threshold: float = 0.35) -> InjectionResult:
    """
    Scan text for patterns indicative of prompt injection.

    Args:
        text: Raw evidence text to scan.
        threshold: Minimum aggregated risk_score (0-1) required to flag
            the text as injection.

    Returns:
        InjectionResult with a risk_score in [0, 1] and the specific
        patterns matched, for audit purposes.
    """
    if not text:
        return InjectionResult(
            is_injection=False,
            risk_score=0.0,
            matched_patterns=[],
            reason="Empty text, nothing to scan.",
        )

    matched: list[str] = []
    score = 0.0

    for category in _CATEGORIES:
        for pattern in category.patterns:
            if pattern.search(text):
                matched.append(f"{category.name}:{pattern.pattern}")
                score += category.weight
                break  # count each category's weight at most once

    risk_score = round(min(score, 1.0), 2)
    is_injection = risk_score >= threshold

    matched_categories = {m.split(":", 1)[0] for m in matched}
    if is_injection:
        reason = (
            f"Matched {len(matched)} suspicious pattern(s) across "
            f"{len(matched_categories)} categor{'y' if len(matched_categories) == 1 else 'ies'} "
            f"({', '.join(sorted(matched_categories))}); "
            f"risk_score={risk_score:.2f} >= threshold={threshold:.2f}."
        )
    else:
        reason = f"No sufficient suspicious patterns found; risk_score={risk_score:.2f}."

    return InjectionResult(
        is_injection=is_injection,
        risk_score=risk_score,
        matched_patterns=matched,
        reason=reason,
    )