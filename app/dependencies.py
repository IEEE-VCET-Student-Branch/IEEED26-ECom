from fastapi import Header, HTTPException
from .utils.idempotency import normalize_key


def require_idempotency_key(
    idempotency_key: str | None = Header(default=None),
) -> str:
    if (
        not idempotency_key
        or not idempotency_key.strip()
        or len(idempotency_key) > 120
    ):
        raise HTTPException(
            400, "Idempotency-Key must be non-blank and at most 120 characters"
        )
    return normalize_key(idempotency_key)


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()