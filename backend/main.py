from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.leads import router as leads_router


app = FastAPI(
    title="End-to-End Real Estate Bot",
    description="Backend API for real estate lead capture and qualification",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "End-to-End Real Estate Bot API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Real Estate Bot API is running"
    }


app.include_router(leads_router)