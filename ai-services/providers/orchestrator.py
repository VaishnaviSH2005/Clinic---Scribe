"""LangGraph-based AI workflow orchestration (PRD Ch3.6): sequences the
Claude-driven reasoning stages (generate_soap -> generate_summary ->
generate_recommendations) over a shared state object, in the fixed order
mandated by PRD Ch17.2. Each node is independent of the others' success —
a failed node records its error in `state["errors"]` and the graph still
proceeds to the next node, so one failing stage never blocks the rest
(Ch17.6 partial-failure isolation).
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from providers.claude import ClaudeClient, ClaudeProviderError


class PipelineState(TypedDict):
    context: dict
    soap: dict | None
    summary: dict | None
    recommendations: dict | None
    risk: dict | None
    errors: dict[str, str]


def _make_node(prompt_name: str, result_key: str, required_keys: tuple[str, ...]):
    async def node(state: PipelineState, claude: ClaudeClient) -> PipelineState:
        try:
            result = await claude.generate_structured(prompt_name, state["context"], required_keys=required_keys)
            state[result_key] = result
        except ClaudeProviderError as exc:
            state["errors"][result_key] = str(exc)
        return state

    return node


_soap_node = _make_node("soap", "soap", ("subjective", "objective", "assessment", "plan"))
_summary_node = _make_node(
    "summary", "summary", ("chief_complaint", "history_of_present_illness", "key_findings", "assessment", "plan")
)
_recommendations_node = _make_node("reasoning", "recommendations", ("possible_diagnoses", "recommended_tests"))
_risk_node = _make_node("risk", "risk", ("red_flags",))


def build_graph(claude: ClaudeClient):
    """Binds `claude` into each node via closures and returns a compiled graph."""

    async def soap_step(state: PipelineState) -> PipelineState:
        return await _soap_node(state, claude)

    async def summary_step(state: PipelineState) -> PipelineState:
        return await _summary_node(state, claude)

    async def recommendations_step(state: PipelineState) -> PipelineState:
        return await _recommendations_node(state, claude)

    async def risk_step(state: PipelineState) -> PipelineState:
        return await _risk_node(state, claude)

    graph = StateGraph(PipelineState)
    graph.add_node("generate_soap", soap_step)
    graph.add_node("generate_summary", summary_step)
    graph.add_node("generate_recommendations", recommendations_step)
    graph.add_node("generate_risk", risk_step)
    graph.add_edge(START, "generate_soap")
    graph.add_edge("generate_soap", "generate_summary")
    graph.add_edge("generate_summary", "generate_recommendations")
    graph.add_edge("generate_recommendations", "generate_risk")
    graph.add_edge("generate_risk", END)
    return graph.compile()


async def run_reasoning_pipeline(claude: ClaudeClient, context: dict) -> PipelineState:
    """Runs generate_soap -> generate_summary -> generate_recommendations
    against `context` (patient + transcript + extracted entities). Returns
    the final state; callers persist whichever of soap/summary/recommendations
    is present and inspect `errors` for stages that failed."""
    compiled = build_graph(claude)
    initial_state: PipelineState = {
        "context": context,
        "soap": None,
        "summary": None,
        "recommendations": None,
        "risk": None,
        "errors": {},
    }
    return await compiled.ainvoke(initial_state)
