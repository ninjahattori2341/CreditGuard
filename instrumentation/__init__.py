"""
PRISM tracing — shared initialisation for Primary AI System.

Import and call the init function that matches your framework ONCE at startup.
All functions read credentials from environment variables only.
Never hardcode secrets here.

Frameworks covered:
    - LangChain          → init_langchain()
    - LangGraph          → init_langgraph(compiled_graph)
    - OpenAI SDK         → trace_openai_call()  (manual wrapper)
    - Anthropic SDK      → trace_anthropic_call()  (manual wrapper)
    - ElevenLabs Voice   → init_elevenlabs_voice()
    - Google ADK         → init_google_adk()
    - LiteLLM            → init_litellm()
    - Custom / generic   → trace_custom_call()
"""

import os
import time
import uuid
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Env-var bootstrap (fail-fast if credentials are missing)
# ---------------------------------------------------------------------------

PRISMTRACE_API_KEY = os.environ.get("PRISMTRACE_API_KEY", "")
PRISMTRACE_PROJECT_ID = os.environ.get(
    "PRISMTRACE_PROJECT_ID", "49b03212-4fb6-4091-9cbe-e8f025d853c1"
)
PRISMTRACE_HOST = os.environ.get(
    "PRISMTRACE_HOST", "https://prism-api-prod.up.railway.app"
)


def _require_key():
    if not PRISMTRACE_API_KEY:
        raise RuntimeError(
            "PRISMTRACE_API_KEY is not set. "
            "Export it or add it to your .env file."
        )


# ===================================================================
# LangChain
# ===================================================================

def init_langchain():
    """
    Return a PRISMtraceCallbackHandler ready to pass as callbacks=[handler].

    Build ONCE at startup; share across requests.  Close at shutdown.
    """
    _require_key()
    from prismtrace import PRISMtraceCallbackHandler

    handler = PRISMtraceCallbackHandler(
        api_key=PRISMTRACE_API_KEY,
        project_id=PRISMTRACE_PROJECT_ID,
        host=PRISMTRACE_HOST,
    )
    return handler


# ===================================================================
# LangGraph
# ===================================================================

def init_langgraph(compiled_graph):
    """
    Wrap a compiled LangGraph graph with PRISM tracing.

    Returns (wrapped_graph, handler).  Close handler at shutdown.
    """
    _require_key()
    from prismtrace import PRISMtraceLangGraphHandler, wrap_langgraph

    handler = PRISMtraceLangGraphHandler(
        api_key=PRISMTRACE_API_KEY,
        project_id=PRISMTRACE_PROJECT_ID,
        host=PRISMTRACE_HOST,
        agent_name="primary-ai-graph",
    )
    wrapped = wrap_langgraph(compiled_graph, handler)
    return wrapped, handler


# ===================================================================
# OpenAI SDK  (manual trace wrapper)
# ===================================================================

def trace_openai_call(
    client,
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    session_id: Optional[str] = None,
    **kwargs,
):
    """
    Call OpenAI and emit a PRISM trace for the round-trip.

    Usage:
        from openai import OpenAI
        client = OpenAI()
        result = trace_openai_call(client, [{"role":"user","content":"hi"}])
    """
    _require_key()
    import prismtrace

    sid = session_id or str(uuid.uuid4())
    start = time.perf_counter()

    with prismtrace.session(sid):
        pt = prismtrace.PRISMtrace(
            api_key=PRISMTRACE_API_KEY,
            host=PRISMTRACE_HOST,
            project_id=PRISMTRACE_PROJECT_ID,
        )
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, **kwargs
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            output_text = response.choices[0].message.content or ""
            pt.trace_llm(
                model=model,
                input_messages=messages,
                output_message=output_text,
                latency_ms=latency_ms,
                session_id=sid,
            )
            return response
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            pt.trace_llm(
                model=model,
                input_messages=messages,
                output_message=f"ERROR: {exc}",
                latency_ms=latency_ms,
                session_id=sid,
            )
            raise


# ===================================================================
# Anthropic SDK  (manual trace wrapper)
# ===================================================================

def trace_anthropic_call(
    client,
    messages: List[Dict[str, str]],
    model: str = "claude-sonnet-4-20250514",
    session_id: Optional[str] = None,
    **kwargs,
):
    """
    Call Anthropic and emit a PRISM trace.
    """
    _require_key()
    import prismtrace

    sid = session_id or str(uuid.uuid4())
    start = time.perf_counter()

    with prismtrace.session(sid):
        pt = prismtrace.PRISMtrace(
            api_key=PRISMTRACE_API_KEY,
            host=PRISMTRACE_HOST,
            project_id=PRISMTRACE_PROJECT_ID,
        )
        try:
            response = client.messages.create(
                model=model, messages=messages, **kwargs
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            output_text = response.content[0].text if response.content else ""
            pt.trace_llm(
                model=model,
                input_messages=messages,
                output_message=output_text,
                latency_ms=latency_ms,
                session_id=sid,
            )
            return response
        except Exception as exc:
            latency_ms = int((time.perf_counter() - start) * 1000)
            pt.trace_llm(
                model=model,
                input_messages=messages,
                output_message=f"ERROR: {exc}",
                latency_ms=latency_ms,
                session_id=sid,
            )
            raise


# ===================================================================
# ElevenLabs Voice  (SDK live tracing — Option B)
# ===================================================================

def init_elevenlabs_voice(agent_name: str = "Support line"):
    """
    Return a PRISMtraceVoiceTracer.  Use its .callbacks() with Conversation().
    Call tracer.finalize(conversation.wait_for_session_end()) when the call ends.
    """
    _require_key()
    from prismtrace import PRISMtraceVoiceTracer

    tracer = PRISMtraceVoiceTracer(
        api_key=PRISMTRACE_API_KEY,
        project_id=PRISMTRACE_PROJECT_ID,
        endpoint=PRISMTRACE_HOST,
        agent_name=agent_name,
    )
    return tracer


# ===================================================================
# Google ADK
# ===================================================================

def init_google_adk():
    """
    Return a PRISMtraceADKAdapter for Google Agent Development Kit agents.
    """
    _require_key()
    from prismtrace.google_adk import PRISMtraceADKAdapter

    adapter = PRISMtraceADKAdapter(
        api_key=PRISMTRACE_API_KEY,
        project_id=PRISMTRACE_PROJECT_ID,
        host=PRISMTRACE_HOST,
    )
    return adapter


# ===================================================================
# LiteLLM
# ===================================================================

def init_litellm():
    """
    Install the PRISM callback into LiteLLM.  Call once at startup.
    Every model LiteLLM routes to is then traced automatically.
    """
    _require_key()
    os.environ.setdefault("PRISMTRACE_API_KEY", PRISMTRACE_API_KEY)
    os.environ.setdefault("PRISMTRACE_PROJECT_ID", PRISMTRACE_PROJECT_ID)
    os.environ.setdefault("PRISMTRACE_HOST", PRISMTRACE_HOST)
    from prismtrace.litellm_callback import install_litellm
    install_litellm()


# ===================================================================
# Custom / generic  (manual trace for any call)
# ===================================================================

def trace_custom_call(
    model: str,
    input_messages: List[Dict[str, str]],
    output_message: str,
    latency_ms: int,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Emit a single PRISM trace for any model/tool call not covered above.
    """
    _require_key()
    import prismtrace

    sid = session_id or str(uuid.uuid4())
    with prismtrace.session(sid):
        pt = prismtrace.PRISMtrace(
            api_key=PRISMTRACE_API_KEY,
            host=PRISMTRACE_HOST,
            project_id=PRISMTRACE_PROJECT_ID,
        )
        pt.trace_llm(
            model=model,
            input_messages=input_messages,
            output_message=output_message,
            latency_ms=latency_ms,
            session_id=sid,
        )
