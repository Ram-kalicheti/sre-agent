from datetime import datetime, timezone
import structlog
from agent.state import IncidentState

log = structlog.get_logger()


def post_mortem(state: IncidentState) -> dict:
    resolved_at = datetime.now(timezone.utc).isoformat()

    report = (
        f"# Incident Post-Mortem\n"
        f"**ID:** {state['incident_id']}\n"
        f"**Alert:** {state['alert_name']}\n"
        f"**Namespace:** {state['namespace']}\n"
        f"**Pod:** {state['pod_name']}\n"
        f"**Severity:** {state['severity']}\n\n"
        f"## Root Cause\n{state.get('root_cause', 'undetermined')}\n\n"
        f"## Diagnosis\n{state.get('diagnosis', 'N/A')}\n\n"
        f"## Action Taken\n{state.get('action_taken', 'none')}\n\n"
        f"## Resolution\n"
        f"Success: {state.get('remediation_success', False)}\n"
        f"Resolved at: {resolved_at}\n"
    )

    log.info(
        "post_mortem_complete",
        incident_id=state["incident_id"],
        resolved_at=resolved_at,
        success=state.get("remediation_success"),
    )

    return {
        "post_mortem_report": report,
        "resolved_at": resolved_at,
    }