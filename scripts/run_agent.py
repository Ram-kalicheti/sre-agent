"""
Run with: python scripts/run_agent.py
Tests that the graph compiles and both paths execute without errors.
"""
import uuid
from agent.graph import sre_agent


def make_incident(alert_name: str, severity: str = "warning") -> dict:
    return {
        "incident_id": str(uuid.uuid4()),
        "alert_name": alert_name,
        "namespace": "production",
        "pod_name": "api-server-7d9f8b-xkz2p",
        "severity": severity,
        "raw_payload": {
            "alert_name": alert_name,
            "namespace": "production",
            "pod_name": "api-server-7d9f8b-xkz2p",
            "severity": severity,
        },
        "runbook_content": None,
        "runbook_source": None,
        "diagnosis": None,
        "root_cause": None,
        "confidence_score": None,
        "action_taken": None,
        "remediation_success": None,
        "post_mortem_report": None,
        "resolved_at": None,
        "error": None,
        "should_escalate": False,
    }


if __name__ == "__main__":
    print("=== Test 1: OOMKilled (normal path — all 5 nodes) ===")
    result = sre_agent.invoke(make_incident("OOMKilled"))
    print(result["post_mortem_report"])

    print("\n=== Test 2: NodeFailure critical (escalation — skips to post_mortem) ===")
    result = sre_agent.invoke(make_incident("NodeFailure", severity="critical"))
    print(result["post_mortem_report"])