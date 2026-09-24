from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.init_db import create_tables
from app.api.v1.router import v1_router

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION
)

# Configure CORS for Driver Portal and admin dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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