from sqlalchemy.orm import Session
from ..models import Order

MAX_IDEMPOTENCY_KEY_LENGTH = 120


def normalize_key(key: str) -> str:
    """Return the canonical form of a logical idempotency key.

    Keys are case-insensitive and surrounding whitespace is ignored. The
    canonical value is used for both lookup and persistence so a retry cannot
    bypass the existing-order lookup.
    """
    return key.strip().lower()


def find_order(db: Session, key: str) -> Order | None:
    return db.query(Order).filter(Order.idempotency_key == normalize_key(key)).first()


def key_length(key: str) -> int:
    return len(normalize_key(key))
