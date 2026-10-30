from sqlalchemy.orm import Session
from ..models import Order


def find_order(db: Session, key: str) -> Order | None:
    if not key:
        return None
    normalized = key.strip().lower()
    return db.query(Order).filter(Order.idempotency_key == normalized).first()


def key_length(key: str) -> int:
    return len(key.strip()) if key else 0
