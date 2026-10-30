from sqlalchemy.orm import Session
from ..models import Order


def normalise_key(key: str) -> str:
    """Return the canonical form of an idempotency key: stripped and lower-cased."""
    return key.strip().lower()


def find_order(db: Session, key: str) -> Order | None:
    return db.query(Order).filter(Order.idempotency_key == normalise_key(key)).first()


def key_length(key: str) -> int:
    return len(key)
