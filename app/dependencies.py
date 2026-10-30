from fastapi import Header, HTTPException


def require_idempotency_key(
    idempotency_key: str | None = Header(default=None),
) -> str:
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required",
        )

    idempotency_key = idempotency_key.strip()

    if len(idempotency_key) > 120:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header must not exceed 120 characters",
        )

    return idempotency_key


def validate_customer_id(customer_id: str) -> str:
    customer_id = customer_id.strip()

    if not customer_id:
        raise HTTPException(
            status_code=400,
            detail="Customer ID cannot be empty",
        )

    return customer_id
