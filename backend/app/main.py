import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the root of the project is in PYTHONPATH so `ml.src` imports work correctly.
# The `backend` directory is inside the project root, so we add the parent of `backend`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.config.settings import get_settings
from app.api.routes import health, reports, incidents, allocations, needs, resources, agents

app = FastAPI(
    title="PS20 - Agentic Disaster Relief & Emergency Resource Coordinator",
    description="Integration API layer for ML models and LangGraph modules.",
    version="1.0.0"
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(reports.router)
app.include_router(incidents.router)
app.include_router(allocations.router)
app.include_router(needs.router)
app.include_router(resources.router)
app.include_router(agents.router)
