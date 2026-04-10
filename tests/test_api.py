from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "Talk2Shell" in response.text


def test_analyze_endpoint_returns_translation():
    response = client.post("/api/analyze", json={"instruction": "list processes", "shell": "powershell"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["translation"]["actions"][0]["commands"]["powershell"] == "Get-Process"


def test_run_endpoint_handles_dry_run():
    response = client.post(
        "/api/run",
        json={"instruction": "show running processes", "shell": "bash", "dry_run": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["execution"]["dry_run"] is True


def test_analyze_endpoint_returns_automation_plan():
    response = client.post(
        "/api/analyze",
        json={"instruction": "download python and install requirements", "shell": "powershell"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["automation"]["category"] == "system_setup"


def test_browser_automation_plan_runs_in_dry_run_preview():
    response = client.post(
        "/api/run",
        json={
            "instruction": "open whatsapp and send a message to John saying hello",
            "shell": "powershell",
            "confirm_risky": True,
            "dry_run": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis"]["automation"]["category"] == "browser_automation"
    assert payload["execution"]["dry_run"] is True
    assert len(payload["execution"]["steps"]) == 3
    assert payload["execution"]["steps"][0]["status"] == "planned"


def test_feedback_and_learned_endpoints():
    feedback_response = client.post(
        "/api/feedback",
        json={
            "instruction": "show active processes",
            "shell": "powershell",
            "commands": ["Get-Process"],
        },
    )
    assert feedback_response.status_code == 200
    assert feedback_response.json()["ok"] is True

    learned_response = client.get("/api/learned")
    assert learned_response.status_code == 200
    payload = learned_response.json()
    assert "items" in payload


def test_capabilities_endpoint():
    response = client.get("/api/capabilities")
    assert response.status_code == 200
    payload = response.json()
    assert "ai_available" in payload
    assert "learned_count" in payload
    assert "automation_categories" in payload
    assert "pending_approvals" in payload


def test_profile_influences_analysis():
    response = client.post(
        "/api/analyze",
        json={"instruction": "show system info", "shell": "powershell", "profile": "power_user"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["safety"]["blocked"] is False


def test_audit_endpoint_returns_events():
    response = client.get("/api/audit")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload


def test_approval_queue_supports_stepwise_review():
    run_response = client.post(
        "/api/run",
        json={
            "instruction": "install python and install requirements",
            "shell": "bash",
            "dry_run": True,
        },
    )
    assert run_response.status_code == 409
    run_payload = run_response.json()
    approval = run_payload["approval"]
    approval_id = approval["id"]
    assert len(approval["steps"]) >= 2

    fetched_response = client.get(f"/api/approvals/{approval_id}")
    assert fetched_response.status_code == 200
    assert fetched_response.json()["status"] == "pending"

    first_review = client.post(f"/api/approvals/{approval_id}/approve", json={"step_indexes": [0]})
    assert first_review.status_code == 200
    assert first_review.json()["approval"]["status"] == "pending"

    final_review = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"step_indexes": [1], "execute_after": True, "dry_run": True},
    )
    assert final_review.status_code == 200
    final_payload = final_review.json()
    assert final_payload["approval"]["status"] == "executed"
    assert final_payload["execution"]["dry_run"] is True

    queue_response = client.get("/api/approvals?status=pending")
    assert queue_response.status_code == 200
    assert isinstance(queue_response.json()["items"], list)
