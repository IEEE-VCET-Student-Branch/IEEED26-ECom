from dataclasses import dataclass
from ..models import CartItem


@dataclass(frozen=True)
class PriceBreakdown:
    subtotal_minor: int
    discount_minor: int
    total_minor: int


def calculate(items: list[CartItem], discount_code: str | None = None) -> PriceBreakdown:
    subtotal = sum(item.product.price_minor * item.quantity for item in items)
    discount = discount_for(subtotal, discount_code)
    return PriceBreakdown(subtotal, discount, subtotal - discount)


def discount_for(subtotal_minor: int, discount_code: str | None) -> int:
    return subtotal_minor // 10 if discount_code and discount_code.strip().upper() == "WELCOME10" else 0
