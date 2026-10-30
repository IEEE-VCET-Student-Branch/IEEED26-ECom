from pathlib import Path
from app.config import get_settings
from app.database import init_db
from app.models import Base
from app.database import engine


def reset_db() -> None:
    db_url = get_settings().database_url
    if db_url.startswith("sqlite:///"):
        db_file = db_url.removeprefix("sqlite:///")
        if db_file != ":memory:":
            Path(db_file).unlink(missing_ok=True)
    Base.metadata.drop_all(engine)
    init_db()


if __name__ == "__main__":
    reset_db()
    print("Database reset")
