# Project Issues and Proposed Fixes

## Overview
This document outlines identified issues in the `IEEED26-ECom` project, primarily related to checkout idempotency.

## Issues

### 1. Inconsistent Idempotency Key Handling (Duplicate Orders)
**Description:** The application stores `idempotency_key` in lowercase (`key.lower()`), but the lookup function (`find_order`) queries the database using the raw key string. This mismatch causes the system to fail to recognize previous requests, leading to duplicate orders if a client retries.

**Fix:** Normalize the idempotency key consistently.
- Update `app/utils/idempotency.py` to normalize the key before querying.
- Ensure `app/services/order_service.py` uses the same normalization logic.

### 2. Missing Key Normalization
**Description:** The `require_idempotency_key` dependency does not strip whitespace from the `Idempotency-Key` header. Clients (like the mobile client) might send the key with extra whitespace, which results in a new, distinct key, bypassing the intended idempotency check.

**Fix:** Add whitespace stripping to the `require_idempotency_key` dependency.

---

## Proposed Changes

### `app/dependencies.py`
```python
def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if not idempotency_key or len(idempotency_key.strip()) > 120 or not idempotency_key.strip():
        raise HTTPException(400, "Idempotency-Key header is required")
    return idempotency_key.strip()
```

### `app/utils/idempotency.py`
```python
def find_order(db: Session, key: str) -> Order | None:
    # Normalize to lowercase as it is stored that way
    return db.query(Order).filter(Order.idempotency_key == key.lower().strip()).first()
```
