"""Optional LangGraph wrapper. The crew list works even if LangGraph is not installed."""

from __future__ import annotations

from typing import TypedDict

from film_platform.crew import CREW


class FilmState(TypedDict, total=False):
    script: str
    locked: bool
    order: str
    takes: list[str]
    kept: str
    step: str


def build_graph():
    """Return a LangGraph that stops before drawing until the hero is locked."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as error:
        raise RuntimeError("Install langgraph to run this graph. The crew list still works without it.") from error

    def mark(step_id: str):
        def _run(state: FilmState) -> FilmState:
            return {"step": step_id}

        return _run

    graph = StateGraph(FilmState)
    for step in CREW:
        graph.add_node(step.id, mark(step.id))
    graph.add_edge(START, CREW[0].id)
    for left, right in zip(CREW, CREW[1:]):
        if left.id == "you_lock":
            graph.add_conditional_edges(
                left.id,
                lambda state: "order" if state.get("locked") else END,
                {"order": "order", END: END},
            )
        else:
            graph.add_edge(left.id, right.id)
    graph.add_edge(CREW[-1].id, END)
    return graph.compile()
