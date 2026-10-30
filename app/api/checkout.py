from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import require_idempotency_key
from ..schemas import CheckoutIn, OrderOut
from ..services.order_service import create_order
router = APIRouter(prefix="/checkout", tags=["checkout"])

# Checkout is intentionally a single command endpoint.


@router.post("", response_model=OrderOut)
@router.post("/", response_model=OrderOut, include_in_schema=False)
def checkout(payload: CheckoutIn, key: str = Depends(require_idempotency_key), db: Session = Depends(get_db)):
    return create_order(db, payload, key)
