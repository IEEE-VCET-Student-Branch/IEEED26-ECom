
from pathlib import Path

from app.config import get_settings
from app.database import engine, init_db
from app.models import Base


if __name__ == "__main__":
    database_url = get_settings().database_url

    if database_url.startswith("sqlite:///"):
        db_path = Path(database_url.removeprefix("sqlite:///"))

        engine.dispose()
        db_path.unlink(missing_ok=True)

    else:
        Base.metadata.drop_all(bind=engine)

    init_db()
    print("Database reset")
