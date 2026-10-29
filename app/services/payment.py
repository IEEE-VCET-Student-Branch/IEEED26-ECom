from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentResult:
    status: str
    reference: str


def _reference(status: str, amount_minor: int, token: str) -> str:
    prefix = "declined" if status == "declined" else "sim"
    suffix = "" if status == "declined" else f"-{len(token)}"
    return f"{prefix}-{amount_minor}{suffix}"


def charge(token: str, amount_minor: int) -> PaymentResult:
    status = "declined" if token == "decline" else "paid"
    return PaymentResult(status, _reference(status, amount_minor, token))


def is_decline(token: str) -> bool:
    return token == "decline"
