from fastapi import FastAPI
from src.api.users import router as users_router
from src.api.auth import router as auth_router
from src.api.projects import router as projects_router
from src.api.api_keys import router as api_keys_router
from src.api.service_ping import router as service_router

app = FastAPI(
    title="Lariba Cloud API",
    description="Backend API for Lariba Cloud Platform",
    version="0.1.0",
)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(api_keys_router)
app.include_router(service_router)

@app.get("/")
def root():
    return {"message": "Welcome to Lariba Cloud API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
