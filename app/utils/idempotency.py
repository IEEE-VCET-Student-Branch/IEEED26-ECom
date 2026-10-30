from sqlalchemy.orm import Session
from ..models import Order


def normalize_key(key: str) -> str:
    return key.strip().lower()


def find_order(db: Session, key: str) -> Order | None:
    return db.query(Order).filter(Order.idempotency_key == normalize_key(key)).first()


def key_length(key: str) -> int:
    return len(key)
