from src.database.db import Base, engine
from src.models.user import User  # noqa: F401

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
