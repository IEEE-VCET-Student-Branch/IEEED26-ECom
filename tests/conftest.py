import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    from app.config import get_settings
    get_settings.cache_clear()
    import app.database as database
    database.engine.dispose()
    database.engine = database.create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    database.SessionLocal.configure(bind=database.engine)
    from app.main import app
    from app.database import init_db
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded(client):
    from app.database import SessionLocal
    from app.models import Product
    db = SessionLocal()
    db.add_all([
        Product(sku="NST-COFFEE", name="Northstar Coffee", description="Beans", price_minor=1299, inventory=20),
        Product(sku="NST-MUG", name="Enamel Camp Mug", description="Mug", price_minor=1899, inventory=15),
    ])
    db.commit()
    db.close()
    return client

