import structlog
from agent.state import IncidentState
from rag.retriever import RunbookRetriever

log = structlog.get_logger()

_retriever: RunbookRetriever | None = None


def _get_retriever() -> RunbookRetriever:
    # lazy init — avoids loading Azure clients at import time during graph compilation
    global _retriever
    if _retriever is None:
        _retriever = RunbookRetriever()
    return _retriever


def _build_query(state: IncidentState) -> str:
    # combining alert name + namespace lets BM25 match exact runbook titles
    # while the vector component covers paraphrased or partial descriptions
    return f"{state['alert_name']} namespace={state['namespace']} pod={state['pod_name']}"


def retrieve_runbook(state: IncidentState) -> dict:
    log.info(
        "runbook_retrieval_started",
        alert_name=state["alert_name"],
        incident_id=state["incident_id"],
    )

    retriever = _get_retriever()
    query = _build_query(state)
    hits = retriever.search(query, top_k=3)

    if not hits:
        log.warning("no_runbooks_found", query=query)
        return {
            "runbook_content": "No matching runbook found for this incident.",
            "runbook_source": None,
        }

    top = hits[0]

    # include all hits so diagnose node has context beyond just the top match
    combined_content = "\n\n---\n\n".join(
        f"## {h['title']} (score: {h['score']:.3f})\n\n{h['content']}" for h in hits
    )

    log.info(
        "runbook_retrieval_complete",
        top_runbook=top["title"],
        top_score=top["score"],
        num_hits=len(hits),
    )

    return {
        "runbook_content": combined_content,
        "runbook_source": top["id"],
    }