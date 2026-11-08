from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.init_db import create_tables
from app.api.v1.router import v1_router

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION
)

# Configure CORS for Driver Portal, admin dashboard, and CCTV viewers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "*",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def add_private_network_access_header(request, call_next):
    """Support Chrome Private Network Access (PNA) preflights from local web pages."""
    if request.method == "OPTIONS" and "access-control-request-private-network" in request.headers:
        from starlette.responses import Response
        response = Response(status_code=200)
        origin = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = request.headers.get("access-control-request-headers", "*")
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response

    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


@app.on_event("startup")
def on_startup():
    """
    Runs once when the server starts.
    Creates all database tables if they don't already exist.
    """
    create_tables()


# Register all v1 API routes
app.include_router(v1_router)


@app.get("/")
def root():
    return {
        "message": "Aswan SmartCurbs AI Backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }