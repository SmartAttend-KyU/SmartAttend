from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import attendance, auth, health
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="SmartAttend API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")


@app.get("/api")
def api_root():
    return {"service": "SmartAttend API", "status": "ok"}
