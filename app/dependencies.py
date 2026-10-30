from fastapi import Header, HTTPException


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if (
        not idempotency_key
        or not idempotency_key.strip()
        or len(idempotency_key.strip()) > 120
    ):
        raise HTTPException(400, "Idempotency-Key header is required")

    return idempotency_key.strip().lower()


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()