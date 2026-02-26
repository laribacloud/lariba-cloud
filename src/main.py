from fastapi import FastAPI
from src.api.api_keys import router as api_keys_router

app = FastAPI(
    title="Lariba Cloud API",
    version="0.1.0",
)

app.include_router(api_keys_router, prefix="/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
