from fastapi import Header, HTTPException


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    stripped = (idempotency_key or "").strip()
    if not stripped or len(idempotency_key) > 120:
        raise HTTPException(400, "Idempotency-Key header is required")
    return idempotency_key


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
