from langgraph.graph import StateGraph, END

from agent.state import IncidentState
from agent.nodes.detect import detect
from agent.nodes.retrieve import retrieve_runbook
from agent.nodes.diagnose import diagnose
from agent.nodes.remediate import remediate
from agent.nodes.post_mortem import post_mortem


def _route_after_detect(state: IncidentState) -> str:
    # NodeFailure + critical has no running pods to inspect
    # skip straight to post_mortem so on-call gets paged immediately
    if state.get("should_escalate"):
        return "post_mortem"
    return "retrieve_runbook"


def build_graph() -> StateGraph:
    graph = StateGraph(IncidentState)

    graph.add_node("detect", detect)
    graph.add_node("retrieve_runbook", retrieve_runbook)
    graph.add_node("diagnose", diagnose)
    graph.add_node("remediate", remediate)
    graph.add_node("post_mortem", post_mortem)

    graph.set_entry_point("detect")

    graph.add_conditional_edges(
        "detect",
        _route_after_detect,
        {
            "retrieve_runbook": "retrieve_runbook",
            "post_mortem": "post_mortem",
        },
    )

    graph.add_edge("retrieve_runbook", "diagnose")
    graph.add_edge("diagnose", "remediate")
    graph.add_edge("remediate", "post_mortem")
    graph.add_edge("post_mortem", END)

    return graph.compile()


# import this in other files — don't call build_graph() twice
sre_agent = build_graph()