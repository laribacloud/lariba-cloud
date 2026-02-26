from fastapi import FastAPI
from src.api.api_keys import router as api_keys_router
from src.api.auth import router as auth_router
from src.api.projects import router as projects_router
from src.api.service_ping import router as service_router
from src.api.service_whoami import router as service_whoami_router

app = FastAPI(
    title="Lariba Cloud API",
    version="0.1.0",
)

app.include_router(api_keys_router, prefix="/v1")
app.include_router(auth_router, prefix="/v1")
app.include_router(projects_router, prefix="/v1")
app.include_router(service_router, prefix="/v1")
app.include_router(service_whoami_router, prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
