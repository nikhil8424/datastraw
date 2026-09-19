# Datastraw Support CRM

A high-velocity, lightweight Customer Support Ticketing CRM built for support engineering and operations teams. Built with **Python + FastAPI**, **SQLite (SQLAlchemy)**, and **HTML/CSS/Tailwind UI** from Stitch design system (*Precision Support Desk*).

---

## 🚀 Features

- **Sequential Auto-Generated Ticket IDs**: Sequential, unique ticket identifiers (`TKT-001`, `TKT-002`, `TKT-003`, etc.).
- **Real-Time Ticket Listing & Search**: Instant case-insensitive search across customer name, ticket ID, email, subject, and issue description.
- **Status Filtering**: Filter by `All`, `Open`, `In Progress`, and `Closed` states.
- **Ticket Intake Flow**: Streamlined creation form with validation, async loading spinner, and toast notification feedback.
- **Detailed Inspector & Timeline**: Dedicated view for customer information, issue context, status management, and chronological thread notes.
- **FastAPI Interactive Docs**: Complete Swagger UI available at `/docs`.
- **Zero Heavyweight Dependencies**: Pure Python + FastAPI + SQLite architecture designed for low latency and easy containerization on Railway.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.12, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2 |
| **Database** | SQLite with persistent volume storage |
| **Frontend** | Semantic HTML5, Vanilla CSS3 / Tailwind CSS, JavaScript |
| **Design System** | *Precision Support Desk* (Inter & JetBrains Mono typography, Slate/Blue palette) |
| **Deployment** | Docker & Railway.app (with persistent volume at `/app/data`) |

---

## 📐 Architecture & Database Schema

### Database Schema (Strictly 2 Tables in SQLite)

```
┌──────────────────────────────────────┐          ┌──────────────────────────────────────┐
│               tickets                │          │                notes                 │
├──────────────────────────────────────┤          ├──────────────────────────────────────┤
│ id: INTEGER PRIMARY KEY              │ 1      * │ id: INTEGER PRIMARY KEY              │
│ ticket_id: TEXT UNIQUE NOT NULL      │<─────────│ ticket_id: TEXT NOT NULL (FK)        │
│ customer_name: TEXT NOT NULL         │          │ note_text: TEXT NOT NULL             │
│ customer_email: TEXT NOT NULL        │          │ created_at: TIMESTAMP NOT NULL       │
│ subject: TEXT NOT NULL               │          └──────────────────────────────────────┘
│ description: TEXT NOT NULL           │
│ status: TEXT NOT NULL                │
│ created_at: TIMESTAMP NOT NULL       │
│ updated_at: TIMESTAMP NOT NULL       │
└──────────────────────────────────────┘
```

- **Allowed Ticket Statuses**: `Open`, `In Progress`, `Closed`.

---

## 📡 API Contract (Strictly 4 Endpoints)

| Method | Endpoint | Description | Request Body / Query Params | Response |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/tickets` | Create a new ticket | `{"customer_name": "...", "customer_email": "...", "subject": "...", "description": "..."}` | `{"ticket_id": "TKT-001", "created_at": "..."}` |
| `GET` | `/api/tickets` | List tickets with filters | `?status=Open&search=Rahul` | `[{"ticket_id": "...", "customer_name": "...", "subject": "...", "status": "...", "created_at": "..."}]` |
| `GET` | `/api/tickets/{ticket_id}` | Get ticket details & notes | None | `{"ticket_id": "...", "customer_name": "...", "customer_email": "...", "subject": "...", "description": "...", "status": "...", "notes": [{"note_text": "...", "created_at": "..."}]}` |
| `PUT` | `/api/tickets/{ticket_id}` | Update status & add note | `{"status": "In Progress", "notes": "Optional note"}` | `{"success": true, "updated_at": "..."}` |

FastAPI Swagger Documentation: **`http://localhost:8000/docs`**

---

## 📁 Project Structure

```
.
├── FRONTEND/                      # Visual source of truth from Stitch
│   ├── index.html                 # Tickets Dashboard
│   ├── dashboard.html             # Dashboard alias
│   ├── ticket-details.html        # Ticket inspection & timeline notes
│   ├── create-ticket.html         # New ticket intake form
│   ├── styles.css                 # Design tokens & shared styles
│   └── logo.svg                   # Brand vector asset
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI initialization & static file serving
│   │   ├── database.py            # SQLite connection & SQLAlchemy session
│   │   ├── models.py              # Ticket and Note models
│   │   ├── schemas.py             # Pydantic request/response schemas
│   │   ├── crud.py                # Database query operations
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── tickets.py         # The 4 REST API routes
│   │
│   ├── data/
│   │   └── tickets.db             # Local SQLite database
│   │
│   ├── requirements.txt           # Python dependencies
│   ├── test_api.py                # Standalone automated API test suite
│   └── .env.example               # Environment variables template
│
├── Dockerfile                     # Production container config for Railway
├── .gitignore
└── README.md
```

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.10+
- `pip`

### 2. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```

Default configuration in `.env`:
```env
DATABASE_URL=sqlite:///./data/tickets.db
PORT=8000
```

### 4. Run Backend & Frontend Server
From the `backend/` directory:
```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser to:
- **Dashboard**: `http://localhost:8000/` (or `http://localhost:8000/index.html`)
- **API Documentation**: `http://localhost:8000/docs`

---

## 🧪 Testing

An automated test suite is included to verify all API contracts, edge cases, and monotonic ID generation:

```bash
python backend/test_api.py
```

### Verified Test Cases:
1. `POST /api/tickets` creates `TKT-001` with status `Open`.
2. `GET /api/tickets` lists newly created tickets.
3. `GET /api/tickets/TKT-001` retrieves all fields and empty notes array.
4. `GET /api/tickets?search=Rahul` searches by customer name.
5. `GET /api/tickets?search=rahul@example.com` searches by email.
6. `GET /api/tickets?search=TKT-001` searches by ticket ID.
7. `GET /api/tickets?search=order` searches subject and description.
8. `GET /api/tickets?status=Open` filters by status.
9. `PUT /api/tickets/TKT-001` updates status and appends a note.
10. `GET /api/tickets/TKT-001` verifies updated status and notes timeline.
11. Monotonic ticket ID progression (`TKT-001` -> `TKT-002` -> `TKT-003`).
12. Validation errors (invalid email format, missing fields, 404 for missing ticket, 400 for invalid status).

---

## 🚂 Railway.app Deployment Guide

### 1. Deploy with Dockerfile
Railway will automatically detect the root `Dockerfile`.

### 2. Configure Persistent Volume
To ensure SQLite database data persists across redeployments:
1. Go to your Railway service **Settings** -> **Volumes**.
2. Add a Volume mounted at:
   ```
   /app/data
   ```
3. Set the Environment Variable in Railway dashboard:
   ```env
   DATABASE_URL=sqlite:////app/data/tickets.db
   ```

### 3. Networking
- Railway automatically provides a `$PORT` environment variable.
- The `Dockerfile` binds Uvicorn to `0.0.0.0:${PORT:-8000}`.
- Generate a Public Domain in Railway **Networking** settings.
