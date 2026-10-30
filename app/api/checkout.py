
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_idempotency_key
from ..schemas import CheckoutIn, OrderOut
from ..services.orders import create_order

router = APIRouter(prefix="/checkout", tags=["checkout"])


@router.post("", response_model=OrderOut)
def checkout(
    payload: CheckoutIn,
    key: str = Depends(require_idempotency_key),
    db: Session = Depends(get_db),
):
    return create_order(db, payload, key)
