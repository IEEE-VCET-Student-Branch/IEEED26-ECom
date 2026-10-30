from fastapi import Header, HTTPException


def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    # Normalize the key to prevent duplicate checkout identities.
    normalized = idempotency_key.strip().lower() if idempotency_key is not None else ""
    if not normalized or len(normalized) > 120:
        raise HTTPException(
            400,
            "Idempotency-Key must be non-blank and at most 120 characters"
        )
    return normalized


def validate_customer_id(customer_id: str) -> str:
    return customer_id.strip()
