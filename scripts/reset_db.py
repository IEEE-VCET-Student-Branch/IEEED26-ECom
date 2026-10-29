from pathlib import Path
from app.config import get_settings
from app.database import init_db
from app.models import Base
from app.database import engine


if __name__ == "__main__":
    if get_settings().database_url.startswith("sqlite:///"):
        Path(get_settings().database_url.removeprefix("sqlite:///")).unlink(missing_ok=True)
    Base.metadata.drop_all(engine)
    init_db()
    print("Database reset")

