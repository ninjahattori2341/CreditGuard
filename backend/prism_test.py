import os
from typing import TypedDict

import prismtrace
from langgraph.graph import StateGraph, START, END
from prismtrace import PRISMtraceLangGraphHandler, wrap_langgraph


class TestState(TypedDict):
    message: str


def hello_node(state: TestState):
    return {
        "message": f"RakshaAI PRISM test received: {state['message']}"
    }


# Build a tiny LangGraph
builder = StateGraph(TestState)

builder.add_node("hello", hello_node)
builder.add_edge(START, "hello")
builder.add_edge("hello", END)

compiled_graph = builder.compile()


# Create the PRISM handler once
handler = PRISMtraceLangGraphHandler(
    api_key=os.environ["PRISMTRACE_API_KEY"],
    project_id=os.environ["PRISMTRACE_PROJECT_ID"],
    host=os.environ.get(
        "PRISMTRACE_HOST",
        "https://prism-api-prod.up.railway.app",
    ),
    agent_name="RakshaAI PRISM Test",
)

# Wrap the LangGraph with PRISM tracing
graph = wrap_langgraph(compiled_graph, handler)


try:
    with prismtrace.session("rakshaai-prism-test-001"):
        result = graph.invoke(
            {"message": "hello from RakshaAI"}
        )

    print("Graph result:")
    print(result)
    print("\nPRISM trace invocation completed.")

finally:
    handler.close()