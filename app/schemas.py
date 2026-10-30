
from pydantic import BaseModel, Field, field_validator


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

    @field_validator("customer_id", "payment_token")
    @classmethod
    def reject_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Must not be empty or whitespace")
        return value


class OrderItemOut(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price_minor: int


class OrderOut(BaseModel):
    id: int
    customer_id: str
    status: str
    subtotal_minor: int
    discount_minor: int
    total_minor: int
    items: list[OrderItemOut]