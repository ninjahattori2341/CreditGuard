from __future__ import annotations

import os
from typing import Any

from instrumentation import trace_custom_call


class PRISMTracer:
    """
    Small adapter around the existing PRISM instrumentation.

    This lets the evaluation system record evaluation events without
    depending directly on the PRISM SDK everywhere.
    """

    def __init__(self, agent_name: str = "RakshaAI Evaluation"):
        self.agent_name = agent_name

    def trace_evaluation(
        self,
        *,
        input_text: str,
        output_text: str,
        session_id: str,
        latency_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Record one evaluation event in PRISM.
        """

        metadata = metadata or {}

        metadata.update(
            {
                "agent_name": self.agent_name,
                "evaluation": True,
            }
        )

        try:
            trace_custom_call(
                model=os.getenv(
                    "LLM_MODEL",
                    "gemini-2.0-flash",
                ),
                input_messages=[
                    {
                        "role": "user",
                        "content": input_text,
                    }
                ],
                output_message=output_text,
                latency_ms=latency_ms,
                session_id=session_id,
                metadata=metadata,
            )

        except Exception as exc:
            # Evaluation should not crash if observability is temporarily
            # unavailable.
            print(f"[PRISM] Trace failed: {exc}")