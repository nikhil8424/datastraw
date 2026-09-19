import os
import sys
from pathlib import Path

# Add backend to sys.path
backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))

test_db_file = backend_path / "data" / "test_tickets.db"
if test_db_file.exists():
    try:
        test_db_file.unlink()
    except Exception:
        pass

os.environ["DATABASE_URL"] = f"sqlite:///{test_db_file}"

from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

# Initialize test database
init_db()

client = TestClient(app)


def run_tests():
    print("=== STARTING API TESTS ===")

    # TEST 1: POST /api/tickets
    payload_1 = {
        "customer_name": "Rahul Sharma",
        "customer_email": "rahul@example.com",
        "subject": "Order not delivered",
        "description": "My order has not arrived."
    }
    res = client.post("/api/tickets", json=payload_1)
    assert res.status_code == 201, f"Test 1 Failed: {res.text}"
    data = res.json()
    assert data["ticket_id"] == "TKT-001", f"Expected TKT-001, got {data['ticket_id']}"
    assert "created_at" in data, "created_at missing"
    print("[PASS] TEST 1 Passed: Created TKT-001")

    # TEST 2: GET /api/tickets
    res = client.get("/api/tickets")
    assert res.status_code == 200, f"Test 2 Failed: {res.text}"
    tickets = res.json()
    assert len(tickets) >= 1, "Expected at least 1 ticket"
    assert tickets[0]["ticket_id"] == "TKT-001"
    assert tickets[0]["customer_name"] == "Rahul Sharma"
    assert tickets[0]["subject"] == "Order not delivered"
    assert tickets[0]["status"] == "Open"
    print("[PASS] TEST 2 Passed: Listed tickets including TKT-001")

    # TEST 3: GET /api/tickets/TKT-001
    res = client.get("/api/tickets/TKT-001")
    assert res.status_code == 200, f"Test 3 Failed: {res.text}"
    ticket = res.json()
    assert ticket["ticket_id"] == "TKT-001"
    assert ticket["customer_name"] == "Rahul Sharma"
    assert ticket["customer_email"] == "rahul@example.com"
    assert ticket["subject"] == "Order not delivered"
    assert ticket["description"] == "My order has not arrived."
    assert ticket["status"] == "Open"
    assert isinstance(ticket["notes"], list)
    assert len(ticket["notes"]) == 0
    print("[PASS] TEST 3 Passed: Retrieved TKT-001 details")

    # TEST 4: GET /api/tickets?search=Rahul
    res = client.get("/api/tickets?search=Rahul")
    assert res.status_code == 200
    assert any(t["ticket_id"] == "TKT-001" for t in res.json())
    print("[PASS] TEST 4 Passed: Search by customer name")

    # TEST 5: GET /api/tickets?search=rahul@example.com
    res = client.get("/api/tickets?search=rahul@example.com")
    assert res.status_code == 200
    assert any(t["ticket_id"] == "TKT-001" for t in res.json())
    print("[PASS] TEST 5 Passed: Search by customer email")

    # TEST 6: GET /api/tickets?search=TKT-001
    res = client.get("/api/tickets?search=TKT-001")
    assert res.status_code == 200
    assert any(t["ticket_id"] == "TKT-001" for t in res.json())
    print("[PASS] TEST 6 Passed: Search by ticket ID")

    # TEST 7: GET /api/tickets?search=order
    res = client.get("/api/tickets?search=order")
    assert res.status_code == 200
    assert any(t["ticket_id"] == "TKT-001" for t in res.json())
    print("[PASS] TEST 7 Passed: Search by subject/description keyword")

    # TEST 8: GET /api/tickets?status=Open
    res = client.get("/api/tickets?status=Open")
    assert res.status_code == 200
    assert any(t["ticket_id"] == "TKT-001" for t in res.json())
    print("[PASS] TEST 8 Passed: Filter by status=Open")

    # TEST 9: PUT /api/tickets/TKT-001
    update_payload = {
        "status": "In Progress",
        "notes": "Contacted logistics team."
    }
    res = client.put("/api/tickets/TKT-001", json=update_payload)
    assert res.status_code == 200, f"Test 9 Failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    assert "updated_at" in data
    print("[PASS] TEST 9 Passed: Updated status and added note")

    # TEST 10: GET /api/tickets/TKT-001 after update
    res = client.get("/api/tickets/TKT-001")
    assert res.status_code == 200
    ticket = res.json()
    assert ticket["status"] == "In Progress"
    assert len(ticket["notes"]) == 1
    assert ticket["notes"][0]["note_text"] == "Contacted logistics team."
    print("[PASS] TEST 10 Passed: Verified updated status and notes timeline")

    # EDGE CASES & VALIDATIONS
    print("\n=== TESTING EDGE CASES ===")

    # Edge Case 1: Sequential ID generation (TKT-002, TKT-003)
    res2 = client.post("/api/tickets", json={
        "customer_name": "Priya Shah",
        "customer_email": "priya@example.com",
        "subject": "Refund request",
        "description": "Item returned, awaiting refund."
    })
    assert res2.status_code == 201
    assert res2.json()["ticket_id"] == "TKT-002"

    res3 = client.post("/api/tickets", json={
        "customer_name": "Amit Patil",
        "customer_email": "amit@example.com",
        "subject": "Login issue",
        "description": "Getting 403 error."
    })
    assert res3.status_code == 201
    assert res3.json()["ticket_id"] == "TKT-003"
    print("[PASS] Edge Case: Monotonic ticket_id generation verified (TKT-002, TKT-003)")

    # Edge Case 2: Invalid email address
    res_invalid_email = client.post("/api/tickets", json={
        "customer_name": "Test User",
        "customer_email": "invalid-email-format",
        "subject": "Test",
        "description": "Test"
    })
    assert res_invalid_email.status_code == 422, "Expected 422 for invalid email"
    print("[PASS] Edge Case: Invalid email validation (422)")

    # Edge Case 3: Missing required fields
    res_missing_field = client.post("/api/tickets", json={
        "customer_name": "Test User"
    })
    assert res_missing_field.status_code == 422
    print("[PASS] Edge Case: Missing required fields (422)")

    # Edge Case 4: Non-existent ticket lookup (404)
    res_404 = client.get("/api/tickets/TKT-999")
    assert res_404.status_code == 404
    print("[PASS] Edge Case: Non-existent ticket 404 response")

    # Edge Case 5: Invalid status update (400)
    res_invalid_status = client.put("/api/tickets/TKT-001", json={
        "status": "InvalidStatus"
    })
    assert res_invalid_status.status_code == 400
    print("[PASS] Edge Case: Invalid status rejected (400)")

    # Edge Case 6: Multiple notes on same ticket
    res_note2 = client.put("/api/tickets/TKT-001", json={
        "status": "Closed",
        "notes": "Refund processed and package delivered."
    })
    assert res_note2.status_code == 200
    res_tkt1 = client.get("/api/tickets/TKT-001")
    assert len(res_tkt1.json()["notes"]) == 2
    assert res_tkt1.json()["status"] == "Closed"
    print("[PASS] Edge Case: Multiple notes appended and ticket Closed")

    # Edge Case 7: Search with no matches
    res_no_match = client.get("/api/tickets?search=nonexistentterm12345")
    assert res_no_match.status_code == 200
    assert len(res_no_match.json()) == 0
    print("[PASS] Edge Case: Search with no matches returns empty array []")

    print("\nALL 10 TESTS + EDGE CASES PASSED PERFECTLY!")

    # Clean up test db file
    try:
        if test_db_file.exists():
            test_db_file.unlink()
    except Exception:
        pass


if __name__ == "__main__":
    run_tests()
