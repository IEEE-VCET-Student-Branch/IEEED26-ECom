## Team

Team name: Clutch Crew

## Summary

This PR resolves checkout idempotency failures, key validation omissions, unconfigurable payment decline tokens, and catalog routing inconsistencies in Northstar Market:
1. Normalizes `Idempotency-Key` casing and whitespace across request dependency parsing, database lookup, and order recording so client retries with varying casing/spacing return the identical order without duplicate inventory deduction or duplicate charges.
2. Enforces non-blank validation for `Idempotency-Key` headers (rejecting empty or whitespace-only keys with HTTP 400).
3. Connects the payment service to `PAYMENT_DECLINE_TOKEN` from application settings rather than hardcoding `"decline"`.
4. Adds route binding for `GET /products` (without trailing slash) to prevent unnecessary 307 redirects.

## Bug inventory

| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|----------|---------|------------|----------|-----|-------------|


| 1 | major | Checkout retries with different casing or surrounding whitespace (e.g., mobile retry after edge timeout) cause duplicate orders, duplicate inventory deduction, or 500 crashes. | `find_order` queried raw un-normalized key against stored lowercased key without trimming; `order_service.create_order` and `dependencies.require_idempotency_key` did not trim or consistently normalize case. | `app/dependencies.py`, `app/utils/idempotency.py`, `app/services/order_service.py` | Strip and lowercase (`.strip().lower()`) idempotency key during dependency validation, database query (`find_order`), and order creation. | Replay tests with mixed casing/whitespace returning identical order without double inventory decrement. |


| 2 | major | Request with whitespace-only `Idempotency-Key` (e.g. `"   "`) was accepted instead of rejected with HTTP 400. | `require_idempotency_key` only checked `not idempotency_key or len(idempotency_key) > 120`. A non-empty whitespace string evaluated as truthy. | `app/dependencies.py:require_idempotency_key` | Validate `not normalized or len(normalized) > 120` after stripping whitespace, raising HTTP 400 if blank. | Checkout test with whitespace-only key asserting HTTP 400. |


| 3 | minor | Setting `PAYMENT_DECLINE_TOKEN` environment variable did not alter decline behavior; provider always checked literal string `"decline"`. | `payment.charge` and `payment.is_decline` hardcoded `token == "decline"` instead of querying `get_settings().payment_decline_token`. | `app/services/payment.py:charge`, `is_decline` | Read decline token via `get_settings().payment_decline_token`. | Test setting `PAYMENT_DECLINE_TOKEN=custom_fail` asserting 402 on `custom_fail` and 200 on other tokens. |


| 4 | minor | `GET /products` triggered HTTP 307 redirect instead of returning catalog directly with 200. | Route was registered solely on `"/"` under prefix `"/products"`, matching `/products/` rather than `/products`. | `app/api/products.py` | Register `@router.get("")` alongside `@router.get("/")`. | `GET /products` with `follow_redirects=False` returning HTTP 200. |

## Defects not fixed

None. All identified defects from the inventory have been addressed.

## Verification

Commands run:

```bash
pytest
```

Visible suite result:

```text
======================== 28 passed, 1 warning in 6.09s ========================
```

Before/after reproduction for each fixed defect:

1. **Idempotency Key Casing & Whitespace Retry:**
   - *Before:* Request with `Idempotency-Key: ORDER-1` followed by retry `Idempotency-Key: order-1` resulted in `find_order` returning `None`, executing payment charge again, creating a duplicate order, and deducting inventory twice.
   - *After:* Second request finds existing order record via normalized key `order-1`, returns identical order body (HTTP 200), leaves inventory deducted exactly once.

2. **Blank Idempotency Key:**
   - *Before:* `POST /checkout` with `Idempotency-Key: "   "` was accepted and processed checkout.
   - *After:* Rejected with HTTP 400 as required by specification.

3. **Configurable Payment Decline Token:**
   - *Before:* With `PAYMENT_DECLINE_TOKEN=custom_fail`, checkout with `custom_fail` was marked "paid" (HTTP 200) instead of declined (HTTP 402).
   - *After:* `custom_fail` returns HTTP 402, leaves cart and inventory untouched, while other tokens succeed.

4. **Product Endpoint Redirect:**
   - *Before:* `GET /products` returned HTTP 307 redirect to `/products/`.
   - *After:* `GET /products` directly returns HTTP 200 with the product list.

## Checklist

- [x] I have read `docs/requirements.md` and `docs/submission.md`
- [x] No changes to `tests/` or `docs/requirements.md`
- [x] A clean checkout runs using the steps in the README
- [x] Retry and decline behavior matches `docs/requirements.md`
- [x] Every item in the bug inventory is fixed or listed under "Defects not fixed"
- [x] No database files, secrets, or generated artifacts are committed
- [x] I understand this PR is evaluated once, when opened, and will not be merged
