# Bug Inventory — Northstar Market

This document lists every defect identified in the codebase, the root cause, the location, and the fix applied.

---

## Bug #1 — [MAJOR] Idempotency Key Lookup Is Not Normalised (Duplicate Orders / 500 on Retry)

**Symptom**
Retrying `POST /checkout` with the same idempotency key sometimes returns `400 "Cart is empty"`,
a `500 Internal Server Error`, or worst case creates a second order, charges the customer
twice, and decrements inventory twice. This is the root cause of Incident #047 and BR-882.

**Root Cause**
`order_service.py` normalises the key before *storing* it (`key.lower()`) but not before
*looking it up*. `find_order(db, key)` queries with the raw, un-normalised key. Because SQLite
uses case-sensitive equality by default, a key stored as `"order-abc"` is never found when the
retry arrives as `"ORDER-ABC"` or `" order-abc "`.

```
# order_service.py (before fix)
order = Order(..., idempotency_key=key.lower())   # stored lower-cased, NOT stripped
...
existing = find_order(db, key)                    # queried with raw key -> MISMATCH
```

**Files changed**
- `app/services/order_service.py`
- `app/utils/idempotency.py`

**Fix**
Added a `normalise_key(key)` helper in `idempotency.py` that strips whitespace and lower-cases
the key. `create_order` now normalises the key once at entry and uses the normalised value for
both the look-up and the stored value.

---

## Bug #2 — [MAJOR] Blank / Whitespace-Only Idempotency Keys Are Accepted

**Symptom**
`POST /checkout` with `Idempotency-Key: "   "` (whitespace only) returns `200 OK` and creates an
order instead of being rejected with `400`.

**Root Cause**
`require_idempotency_key` in `app/dependencies.py` checks `not idempotency_key`, which is `False`
for a non-empty whitespace string — `"   "` is truthy in Python. The validation passes.

```python
# dependencies.py (before fix)
if not idempotency_key or len(idempotency_key) > 120:   # "   " passes this test
    raise HTTPException(400, ...)
```

**Requirement**
> The key must be non-blank and at most 120 characters; otherwise the request is rejected with 400.

**Files changed**
- `app/dependencies.py`

**Fix**
Changed the guard to strip the key before checking truthiness.

---

## Bug #3 — [MAJOR] PAYMENT_DECLINE_TOKEN Environment Variable Is Ignored

**Symptom**
Setting `PAYMENT_DECLINE_TOKEN=anything_else` in the environment has no effect. The payment
provider always declines on the literal string `"decline"` regardless of configuration.

**Root Cause**
`app/services/payment.py` hard-codes the string `"decline"` instead of reading from
`get_settings().payment_decline_token`.

```python
# payment.py (before fix)
def charge(token: str, amount_minor: int) -> PaymentResult:
    status = "declined" if token == "decline" else "paid"   # hard-coded literal
```

**Requirement**
> The token that simulates a decline is read from the `PAYMENT_DECLINE_TOKEN` environment
> setting, which defaults to `decline`.

**Files changed**
- `app/services/payment.py`

**Fix**
`charge()` and `is_decline()` now call `get_settings().payment_decline_token` to obtain the
configured token at call time.

---

## Bug #4 — [MINOR] GET /products Returns 307 Redirect Instead of 200 OK

**Symptom**
A strict HTTP client that calls `GET /products` without a trailing slash receives
`307 Temporary Redirect` to `/products/` instead of `200 OK`.

**Root Cause**
`app/api/products.py` registers the list endpoint as `@router.get("/")` on a router whose prefix
is `/products`. FastAPI therefore mounts the route at `/products/` (with trailing slash). Compare
with `orders.py` which correctly uses `@router.get("")`.

**Files changed**
- `app/api/products.py`

**Fix**
Changed `@router.get("/")` to `@router.get("")` so the route is registered at `/products` directly.

---

## Summary Table

| # | Severity | Symptom | Root Cause | Location | Fix |
|---|----------|---------|------------|----------|-----|
| 1 | Major | Retry creates duplicate order or 500 error | Key stored lower-cased but looked up with raw key | `order_service.py`, `idempotency.py` | Normalise key (strip + lower) before look-up and store |
| 2 | Major | Whitespace-only key accepted with 200 | `not key` is False for `"   "` | `dependencies.py` | Check `.strip()` before truthiness test |
| 3 | Major | Custom PAYMENT_DECLINE_TOKEN ignored | `"decline"` hard-coded in `payment.py` | `payment.py` | Read `get_settings().payment_decline_token` |
| 4 | Minor | `GET /products` returns 307 redirect | Route registered as `"/"` instead of `""` | `products.py` | Change `@router.get("/")` to `@router.get("")` |

---

## Verification

```bash
python -m pytest
```

Expected: all 28 tests pass.
