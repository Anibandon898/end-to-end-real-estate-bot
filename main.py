from fastapi import FastAPI

app = FastAPI(title="End-to-End Real Estate Bot")


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "message": "Real Estate Bot API is running"
    }