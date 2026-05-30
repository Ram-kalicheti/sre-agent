import structlog
from agent.state import IncidentState

log = structlog.get_logger()


def diagnose(state: IncidentState) -> dict:
    log.info(
        "diagnosis_started",
        incident_id=state["incident_id"],
        runbook_source=state.get("runbook_source"),
    )

    return {
        "diagnosis": "Stub diagnosis — reasoning not yet wired.",
        "root_cause": "unknown",
        "confidence_score": 0.0,
    }