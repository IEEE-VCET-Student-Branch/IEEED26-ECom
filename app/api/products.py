from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Product
from ..schemas import ProductOut
router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductOut])
@router.get("/", response_model=list[ProductOut], include_in_schema=False)
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.id).all()


@router.get("/{product_id}", response_model=ProductOut)
@router.get("/{product_id}/", response_model=ProductOut, include_in_schema=False)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product
