import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test-spendlens.db")

import pytest

from backend.db import Base, SessionLocal, engine
from backend.main import seed_store


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_store(db)
    yield
