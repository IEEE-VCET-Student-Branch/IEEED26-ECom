# Comprehensive Bug Report and Fixes

## Overview
This document details all identified bugs, root causes, and implemented fixes for the `IEEED26-ECom` project, focusing primarily on checkout idempotency and key normalization issues.

---

## Identified Bugs & Errors

### 1. Inconsistent Idempotency Key Casing (Duplicate Orders)
- **Description:** The system previously stored `idempotency_key` converted to lowercase (`key.lower()`), but the lookup function (`find_order`) queried the database using the raw, un-normalized key string. 
- **Impact:** Retrying a checkout request with a different key casing (e.g., `KEY-1` vs `key-1`) resulted in a cache miss, causing the application to process the request again and create duplicate orders and duplicate inventory reservations.

### 2. Missing Key Whitespace Normalization
- **Description:** The `require_idempotency_key` dependency did not strip leading or trailing whitespace from the `Idempotency-Key` header. Clients (such as mobile applications) often reassemble or pad headers with whitespace.
- **Impact:** Extra whitespace caused requests with identical logical keys to be treated as distinct new requests, bypassing idempotency guarantees and failing validation when clients sent padded keys.

---

## Implemented Fixes

### 1. Header Validation & Whitespace Stripping (`app/dependencies.py`)
- Updated `require_idempotency_key` to strip whitespace and validate that the stripped key is non-empty and within length limits.
```python
def require_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str:
    if not idempotency_key or len(idempotency_key.strip()) > 120 or not idempotency_key.strip():
        raise HTTPException(400, "Idempotency-Key header is required")
    return idempotency_key.strip()
```

### 2. Consistent Order Key Storage (`app/services/order_service.py`)
- Ensured newly created orders consistently normalize the stored idempotency key via `.lower().strip()`.
```python
order = Order(customer_id=request.customer_id, status=result.status,
              subtotal_minor=quote.subtotal_minor, discount_minor=quote.discount_minor,
              total_minor=quote.total_minor, idempotency_key=key.lower().strip())
```

### 3. Robust Order Lookup (`app/utils/idempotency.py`)
- Updated `find_order` to normalize incoming keys to lowercase and stripped format during database queries.
```python
def find_order(db: Session, key: str) -> Order | None:
    return db.query(Order).filter(Order.idempotency_key == key.lower().strip()).first()
```
