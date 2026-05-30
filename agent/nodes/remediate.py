import structlog
from agent.state import IncidentState

log = structlog.get_logger()


def remediate(state: IncidentState) -> dict:
    log.info(
        "remediation_started",
        incident_id=state["incident_id"],
        root_cause=state.get("root_cause"),
    )

    return {
        "action_taken": "Stub: no remediation action taken.",
        "remediation_success": False,
    }