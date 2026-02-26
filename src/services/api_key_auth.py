from typing import Optional
from datetime import datetime, timezone
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from src.database.deps import get_db
from src.models.api_key import ApiKey
from src.models.project import Project
from src.services.api_keys import hash_api_key


def get_project_from_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Project:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    hashed = hash_api_key(x_api_key)
    key = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    key.last_used_at = datetime.now(timezone.utc)
    db.commit()

    project = db.query(Project).filter(Project.id == key.project_id).first()
    if not project:
        raise HTTPException(status_code=401, detail="Project not found for API key")

    return project
