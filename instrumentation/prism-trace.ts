/**
 * PRISM tracing — TypeScript / Vercel AI SDK helper.
 *
 * Import emitTrace() into your API routes or chat handlers.
 * Reads credentials from environment variables only.
 */

const PRISMTRACE_HOST =
  process.env.PRISMTRACE_HOST ?? "https://prism-api-prod.up.railway.app";
const PRISMTRACE_API_KEY = process.env.PRISMTRACE_API_KEY!;
const PRISMTRACE_PROJECT_ID =
  process.env.PRISMTRACE_PROJECT_ID ??
  "49b03212-4fb6-4091-9cbe-e8f025d853c1";

interface TraceOpts {
  model?: string;
  latencyMs?: number;
  sessionId?: string;
  toolCalls?: Array<{ name: string; input: string; output: string }>;
}

/**
 * Post one trace to PRISM after a model call returns.
 *
 * Await this in serverless so the POST finishes before the function freezes.
 */
export async function emitTrace(
  input: string,
  output: string,
  opts?: TraceOpts
): Promise<void> {
  if (!PRISMTRACE_API_KEY) {
    console.warn("[PRISM] PRISMTRACE_API_KEY is not set — skipping trace.");
    return;
  }

  const res = await fetch(`${PRISMTRACE_HOST}/api/traces`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-PRISMtrace-Key": PRISMTRACE_API_KEY,
    },
    body: JSON.stringify({
      project_id: PRISMTRACE_PROJECT_ID,
      model: opts?.model ?? "gpt-4o-mini",
      input_messages: [{ role: "user", content: input }],
      output_message: output,
      latency_ms: opts?.latencyMs ?? 0,
      session_id: opts?.sessionId,
    }),
  });

  if (!res.ok) {
    const body = await res.text();
    console.error(`[PRISM] ingest ${res.status}: ${body}`);
  }
}
