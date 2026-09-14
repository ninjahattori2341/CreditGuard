# Primary AI System — Agent Instructions

## Project overview

This is the **Primary AI System** repository (devanshghosh6107).
Application types: Chatbot, Voice, Workflow, Document Processing, Assistant, RAG, Multi-Agent.
Frameworks: LangChain, LangGraph, OpenAI SDK, Vercel AI SDK, Google ADK, Anthropic SDK, LiteLLM, OpenTelemetry, Custom.

## Conventions

- Keep secrets out of version control. Use `.env` (untracked) for credentials; `.env.example` for key names.
- Instrumentation lives in `instrumentation/` — one Python module and one TypeScript helper.
- Prefer environment variables for all API keys and configuration.

## PRISM tracing (do not remove)

This project sends traces to PRISM. Env vars: `PRISMTRACE_API_KEY`,
`PRISMTRACE_PROJECT_ID`, `PRISMTRACE_HOST`.

Tracing is currently wired at: `instrumentation/__init__.py`, `instrumentation/prism-trace.ts`, `.env.example`, `AGENTS.md`

**Standing rule.** Whenever you add or change an agent, chain, graph, tool,
retriever, or any entry point that calls a model, wire it to PRISM before you
finish. Unwired code is invisible in the dashboard. If you are unsure whether
something is covered, assume it is not and wire it.
