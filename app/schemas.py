from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    price_minor: int
    inventory: int
    model_config = {"from_attributes": True}


class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=99)


class CartItemOut(BaseModel):
    product_id: int
    sku: str
    name: str
    quantity: int
    unit_price_minor: int
    line_total_minor: int


class CartOut(BaseModel):
    customer_id: str
    items: list[CartItemOut]
    subtotal_minor: int


class HealthOut(BaseModel):
    status: str
    service: str


class CheckoutIn(BaseModel):
    customer_id: str = Field(min_length=1, max_length=80)
    discount_code: str | None = None
    payment_token: str = Field(min_length=1)


class OrderItemOut(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price_minor: int
    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_id: str
    status: str
    subtotal_minor: int
    discount_minor: int
    total_minor: int
    items: list[OrderItemOut]
    model_config = {"from_attributes": True}
