from sqlalchemy.orm import Session
from ..models import Order


def find_order(db: Session, key: str) -> Order | None:
    normalized = key.strip().lower() if key else ""
    return db.query(Order).filter(Order.idempotency_key == normalized).first()


def key_length(key: str) -> int:
    return len(key)
