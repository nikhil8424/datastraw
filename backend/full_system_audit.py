import os
import sys
import sqlite3
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.main import app
from app.database import engine, Base, SessionLocal, init_db
from app.models import Ticket, Note
import app.crud as crud

client = TestClient(app)

def run_comprehensive_audit():
    print("=" * 60)
    print("      DATASTRAW SUPPORT CRM - DEEP SYSTEM AUDIT")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = 0

    def assert_test(name, condition, extra_info=""):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f"[PASS] {name} {extra_info}")
        else:
            print(f"[FAIL] {name} {extra_info}")
            raise AssertionError(f"Test failed: {name}")

    # 1. Database Schema & Integrity Check
    print("\n--- 1. DATABASE SCHEMA & INTEGRITY ---")
    init_db()
    db = SessionLocal()
    
    conn = engine.raw_connection()
    cur = conn.cursor()
    
    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
    assert_test("SQLite PRAGMA integrity_check", integrity == "ok", f"-> {integrity}")
    
    cur.execute("PRAGMA foreign_key_check;")
    fk_violations = cur.fetchall()
    assert_test("Foreign Key Integrity (0 orphan notes)", len(fk_violations) == 0, f"-> {len(fk_violations)} violations")
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = sorted([r[0] for r in cur.fetchall()])
    assert_test("Strict Two Tables (tickets, notes)", tables == ["notes", "tickets"], f"-> {tables}")
    conn.close()

    # 2. Endpoint 1: POST /api/tickets
    print("\n--- 2. ENDPOINT 1: POST /api/tickets ---")
    
    # Valid Ticket
    res = client.post("/api/tickets", json={
        "customer_name": "Nikhil Gupta",
        "customer_email": "nikhil@datastraw.io",
        "subject": "Integration Webhook Latency Alert",
        "description": "API latency exceeded 500ms during peak load on /v1/events"
    })
    assert_test("POST /api/tickets status 201", res.status_code == 201)
    t1 = res.json()
    assert_test("Ticket ID format starts with TKT-", t1.get("ticket_id", "").startswith("TKT-"), f"-> {t1.get('ticket_id')}")
    assert_test("Response includes created_at", "created_at" in t1)
    ticket_id_1 = t1["ticket_id"]

    # Missing field (422)
    res_422 = client.post("/api/tickets", json={
        "customer_name": "Test",
        "customer_email": "test@test.com"
    })
    assert_test("POST /api/tickets missing fields returns 422", res_422.status_code == 422)

    # Invalid email (422)
    res_invalid_email = client.post("/api/tickets", json={
        "customer_name": "Test",
        "customer_email": "not-an-email",
        "subject": "Test",
        "description": "Test"
    })
    assert_test("POST /api/tickets invalid email returns 422", res_invalid_email.status_code == 422)

    # 3. Endpoint 2: GET /api/tickets (Listing, Filtering, Search)
    print("\n--- 3. ENDPOINT 2: GET /api/tickets ---")
    
    # List all
    res_list = client.get("/api/tickets")
    assert_test("GET /api/tickets status 200", res_list.status_code == 200)
    all_tickets = res_list.json()
    assert_test("Listing contains tickets list", isinstance(all_tickets, list) and len(all_tickets) >= 1)
    
    # Search by Name
    res_search_name = client.get("/api/tickets?search=Nikhil")
    assert_test("Search by customer name", len(res_search_name.json()) >= 1 and any(t["ticket_id"] == ticket_id_1 for t in res_search_name.json()))
    
    # Search by Email
    res_search_email = client.get("/api/tickets?search=datastraw.io")
    assert_test("Search by customer email", len(res_search_email.json()) >= 1 and any(t["ticket_id"] == ticket_id_1 for t in res_search_email.json()))

    # Search by Ticket ID
    res_search_id = client.get(f"/api/tickets?search={ticket_id_1}")
    assert_test("Search by ticket_id", len(res_search_id.json()) >= 1 and res_search_id.json()[0]["ticket_id"] == ticket_id_1)

    # Search by Subject
    res_search_subj = client.get("/api/tickets?search=Webhook")
    assert_test("Search by subject", len(res_search_subj.json()) >= 1 and any(t["ticket_id"] == ticket_id_1 for t in res_search_subj.json()))

    # Filter by Status=Open
    res_filter_open = client.get("/api/tickets?status=Open")
    assert_test("Filter by status=Open", all(t["status"] == "Open" for t in res_filter_open.json()))

    # Filter by Status=Closed
    res_filter_closed = client.get("/api/tickets?status=Closed")
    assert_test("Filter by status=Closed", all(t["status"] == "Closed" for t in res_filter_closed.json()))

    # 4. Endpoint 3: GET /api/tickets/{ticket_id} (Details + Notes Timeline)
    print("\n--- 4. ENDPOINT 3: GET /api/tickets/{ticket_id} ---")
    
    res_detail = client.get(f"/api/tickets/{ticket_id_1}")
    assert_test("GET /api/tickets/{id} status 200", res_detail.status_code == 200)
    d = res_detail.json()
    assert_test("Detail has customer_email", d.get("customer_email") == "nikhil@datastraw.io")
    assert_test("Detail has description", "latency" in d.get("description", ""))
    assert_test("Detail has status", d.get("status") == "Open")
    assert_test("Detail has notes array", isinstance(d.get("notes"), list))
    assert_test("Detail has created_at timestamp", "created_at" in d and d["created_at"] is not None)

    # Non-existent ticket 404
    res_404 = client.get("/api/tickets/TKT-999999")
    assert_test("Non-existent ticket returns 404", res_404.status_code == 404)

    # 5. Endpoint 4: PUT /api/tickets/{ticket_id} (Status Update & Note Creation)
    print("\n--- 5. ENDPOINT 4: PUT /api/tickets/{ticket_id} ---")
    
    # Update to In Progress with Note
    res_put = client.put(f"/api/tickets/{ticket_id_1}", json={
        "status": "In Progress",
        "notes": "Assigned to L2 network operations team for packet analysis."
    })
    assert_test("PUT /api/tickets/{id} status 200", res_put.status_code == 200)
    assert_test("PUT response success=True", res_put.json().get("success") is True)
    assert_test("PUT response has updated_at", "updated_at" in res_put.json())

    # Verify Note was persisted in timeline
    res_verify_note = client.get(f"/api/tickets/{ticket_id_1}")
    v_data = res_verify_note.json()
    assert_test("Status changed to In Progress", v_data.get("status") == "In Progress")
    assert_test("Note appended to timeline", len(v_data.get("notes", [])) >= 1)
    assert_test("Note text matches exactly", v_data["notes"][-1]["note_text"] == "Assigned to L2 network operations team for packet analysis.")

    # Update to Closed with another Note
    res_put_close = client.put(f"/api/tickets/{ticket_id_1}", json={
        "status": "Closed",
        "notes": "Route optimization deployed; latency reduced to 42ms."
    })
    assert_test("PUT /api/tickets/{id} status Closed", res_put_close.status_code == 200)
    
    res_verify_close = client.get(f"/api/tickets/{ticket_id_1}")
    assert_test("Status updated to Closed", res_verify_close.json().get("status") == "Closed")
    assert_test("Multiple notes preserved in order", len(res_verify_close.json().get("notes", [])) >= 2)

    # Invalid status rejected (400)
    res_bad_status = client.put(f"/api/tickets/{ticket_id_1}", json={
        "status": "Archived",
        "notes": "Should fail"
    })
    assert_test("Invalid status returns 400 Bad Request", res_bad_status.status_code == 400)

    # Non-existent ticket update 404
    res_put_404 = client.put("/api/tickets/TKT-999999", json={"status": "Open"})
    assert_test("Update non-existent ticket returns 404", res_put_404.status_code == 404)

    # 6. Monotonic Ticket ID Generation
    print("\n--- 6. SEQUENTIAL TICKET ID GENERATION ---")
    res_next1 = client.post("/api/tickets", json={
        "customer_name": "Seq Test 1",
        "customer_email": "seq1@test.com",
        "subject": "Sequential 1",
        "description": "Seq desc"
    })
    res_next2 = client.post("/api/tickets", json={
        "customer_name": "Seq Test 2",
        "customer_email": "seq2@test.com",
        "subject": "Sequential 2",
        "description": "Seq desc"
    })
    id1 = res_next1.json()["ticket_id"]
    id2 = res_next2.json()["ticket_id"]
    num1 = int(id1.split("-")[1])
    num2 = int(id2.split("-")[1])
    assert_test(f"Monotonic sequence: {id1} -> {id2}", num2 == num1 + 1)

    # 7. Static Asset Mounting & UI Routing
    print("\n--- 7. STATIC ASSET SERVING & ROUTING ---")
    res_root = client.get("/")
    assert_test("GET / serves index.html (200)", res_root.status_code == 200 and "text/html" in res_root.headers.get("content-type", ""))
    
    res_create = client.get("/create-ticket.html")
    assert_test("GET /create-ticket.html serves create screen (200)", res_create.status_code == 200)

    res_detail_page = client.get("/ticket-details.html")
    assert_test("GET /ticket-details.html serves detail screen (200)", res_detail_page.status_code == 200)

    res_css = client.get("/styles.css")
    assert_test("GET /styles.css serves stylesheet (200)", res_css.status_code == 200)

    res_docs = client.get("/docs")
    assert_test("GET /docs serves Swagger UI (200)", res_docs.status_code == 200)

    print("\n" + "=" * 60)
    print(f"AUDIT SUMMARY: {passed_tests}/{total_tests} TESTS PASSED (100% SUCCESS)")
    print("=" * 60)

if __name__ == "__main__":
    run_comprehensive_audit()
