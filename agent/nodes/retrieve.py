import structlog
from agent.state import IncidentState

log = structlog.get_logger()

RUNBOOK_STUB = "## Stub Runbook\nNo runbook retrieved — search client not yet wired."


def retrieve_runbook(state: IncidentState) -> dict:
    log.info(
        "runbook_retrieval_started",
        alert_name=state["alert_name"],
        incident_id=state["incident_id"],
    )

    return {
        "runbook_content": RUNBOOK_STUB,
        "runbook_source": "stub-doc-id",
    }