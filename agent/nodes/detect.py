import structlog
from agent.state import IncidentState

log = structlog.get_logger()


def detect(state: IncidentState) -> dict:
    payload = state["raw_payload"]

    alert_name = payload.get("alert_name", "unknown")
    namespace = payload.get("namespace", "default")
    pod_name = payload.get("pod_name", "unknown")
    severity = payload.get("severity", "warning")

    log.info(
        "incident_detected",
        incident_id=state["incident_id"],
        alert_name=alert_name,
        severity=severity,
    )

    # NodeFailure + critical = page immediately, skip the rest of the pipeline
    should_escalate = severity == "critical" and alert_name == "NodeFailure"

    return {
        "alert_name": alert_name,
        "namespace": namespace,
        "pod_name": pod_name,
        "severity": severity,
        "should_escalate": should_escalate,
    }