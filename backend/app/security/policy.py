"""
policy.py

Explicit, simple security policy for RakshaAI.

This is NOT a general-purpose policy engine — just a small, fixed set of
rules that action_authorizer.py consults. Keeping this file simple and
explicit (rather than configurable/dynamic) is a deliberate design choice
for the hackathon prototype.
"""

from __future__ import annotations

from dataclasses import dataclass

# Actions that have real-world consequences and therefore require
# independent authorization before they're allowed to execute.
SENSITIVE_ACTIONS: frozenset[str] = frozenset({
    "close_case",
    "flag_transaction",
    "escalate_case",
})


@dataclass(frozen=True)
class PolicyRules:
    """The fixed set of rules the authorizer enforces."""

    untrusted_evidence_cannot_authorize_sensitive_actions: bool = True
    evidence_cannot_redefine_investigation_goal: bool = True
    sensitive_actions_require_independent_authorization: bool = True
    suspicious_evidence_must_be_quarantined: bool = True
    agent_proposes_policy_decides: bool = True


# Single, fixed policy instance for the hackathon prototype.
ACTIVE_POLICY = PolicyRules()


def is_sensitive_action(action: str) -> bool:
    """Return True if the given action name requires independent authorization."""
    return action in SENSITIVE_ACTIONS