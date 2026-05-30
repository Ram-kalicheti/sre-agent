from typing import TypedDict, Optional


class IncidentState(TypedDict):
    # raw input from SQS
    incident_id: str
    alert_name: str
    namespace: str
    pod_name: str
    severity: str
    raw_payload: dict

    # populated by retrieve node
    runbook_content: Optional[str]
    runbook_source: Optional[str]

    # populated by diagnose node
    diagnosis: Optional[str]
    root_cause: Optional[str]
    confidence_score: Optional[float]

    # populated by remediate node
    action_taken: Optional[str]
    remediation_success: Optional[bool]

    # populated by post_mortem node
    post_mortem_report: Optional[str]
    resolved_at: Optional[str]

    # routing
    error: Optional[str]
    should_escalate: bool