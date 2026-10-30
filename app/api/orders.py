from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Order
from ..schemas import OrderOut
router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.get("", response_model=list[OrderOut])
@router.get("/", response_model=list[OrderOut], include_in_schema=False)
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).order_by(Order.id).all()
