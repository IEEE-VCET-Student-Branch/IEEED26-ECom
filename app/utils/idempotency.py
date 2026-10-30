from sqlalchemy.orm import Session
from ..models import Order


def find_order(db: Session, key: str) -> Order | None:
    return db.query(Order).filter(Order.idempotency_key == key.lower().strip()).first()


def key_length(key: str) -> int:
    return len(key)
