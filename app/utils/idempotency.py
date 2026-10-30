
from sqlalchemy.orm import Session

from ..models import Order


def normalize_key(key: str) -> str:
    """Normalize keys for case-insensitive and whitespace-insensitive matching."""
    return key.strip().lower()


def key_length(key: str) -> int:
    """Return the length of the normalized key."""
    return len(normalize_key(key))


def find_order(db: Session, key: str) -> Order | None:
    """Find an existing order using its normalized idempotency key."""
    normalized_key = normalize_key(key)

    return (
        db.query(Order)
        .filter(Order.idempotency_key == normalized_key)
        .first()
    )
