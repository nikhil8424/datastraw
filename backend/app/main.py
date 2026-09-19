import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import init_db
from .routes.tickets import router as tickets_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="Datastraw Support CRM API",
    description="Customer Support Ticket CRM API - Datastraw Technologies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Tickets Router
app.include_router(tickets_router)

# Resolve FRONTEND path relative to project root or local directory
# In production container: /app/FRONTEND
# In local development: ../FRONTEND relative to app/ or ./FRONTEND relative to project root
possible_frontend_paths = [
    Path(__file__).resolve().parent.parent.parent / "FRONTEND",  # local: <root>/FRONTEND
    Path("/app/FRONTEND"),                                       # Docker production
    Path(__file__).resolve().parent.parent / "FRONTEND",         # backend/FRONTEND fallback
    Path("./FRONTEND"),
]

frontend_dir = None
for p in possible_frontend_paths:
    if p.exists() and p.is_dir():
        frontend_dir = p
        break

if frontend_dir:
    # Serve static assets from FRONTEND
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(frontend_dir / "index.html")

    @app.get("/{page_name}.html", include_in_schema=False)
    async def serve_html_page(page_name: str):
        page_file = frontend_dir / f"{page_name}.html"
        if page_file.exists():
            return FileResponse(page_file)
        return FileResponse(frontend_dir / "index.html")

    @app.get("/styles.css", include_in_schema=False)
    async def serve_styles():
        return FileResponse(frontend_dir / "styles.css")

    @app.get("/logo.svg", include_in_schema=False)
    async def serve_logo():
        return FileResponse(frontend_dir / "logo.svg")
