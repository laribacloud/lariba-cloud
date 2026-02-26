from fastapi import FastAPI

from src.api.auth import router as auth_router
from src.api.projects import router as projects_router
from src.api.api_keys import router as api_keys_router
# 👇 ADD THIS
from src.api.organizations import router as organizations_router

app = FastAPI()

app.include_router(auth_router, prefix="/v1")
app.include_router(projects_router, prefix="/v1")
app.include_router(api_keys_router, prefix="/v1")
# 👇 ADD THIS
app.include_router(organizations_router, prefix="/v1")