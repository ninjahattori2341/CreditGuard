from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    response: str
    risk_level: str
    reasoning: str
    recommended_action: str
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class SecurityResult:
    injection_detected: bool = False
    injection_score: float = 0.0
    quarantined: bool = False
    action_allowed: bool = True
    action_blocked: bool = False
    risk_score: float = 0.0
    risk_level: str = "LOW"
    source_trust: str = "TRUSTED"
    reason: str = ""


@dataclass
class EvaluationResult:
    case_id: str
    category: str
    mode: str
    agent: AgentResult
    security: SecurityResult
    attack_succeeded: bool
    unauthorized_tool_call: bool
    correct_fraud_decision: bool
    false_positive: bool
    injection_detected: bool
    action_blocked: bool
    passed: bool
    reason: str = ""