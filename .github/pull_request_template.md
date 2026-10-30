## Team

Team name:Full Stack Attack

## Summary

What was broken, and what this PR changes.

## Bug inventory

List every defect found, major and minor, including ones not fixed here. Add rows as needed.

| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|----------|---------|------------|----------|-----|-------------|
| # | Severity | Symptom | Root cause | Location | Fix | Verified by |
|---|---|---|---|---|---|---|
| 1 | Major | Application import fails | Missing checkout module | `app/api/checkout.py` | Create checkout API endpoint | Pending |
| 2 | Major | Order service import fails | Missing idempotency utility | `app/utils/idempotency.py` | Implement idempotency lookup | Pending |
| 3 | Major | Custom payment decline token is ignored | Hardcoded `"decline"` token | `app/services/payment.py` | Use `PAYMENT_DECLINE_TOKEN` setting | Pending |
| 4 | Major | Same logical idempotency key may not match consistently | Inconsistent key normalization | `app/services/orders.py`, `app/utils/idempotency.py` | Normalize keys before lookup and storage | Pending |

## Defects not fixed

## Defects not fixed

1. **Missing checkout API module:** The checkout endpoint has not yet been implemented and verified. It remains pending integration with the existing order service.

2. **Missing idempotency utility:** The utility for finding existing orders using normalized idempotency keys has not yet been fully implemented and tested.

3. **Payment decline configuration:** The payment service still needs to be updated and verified to use the `PAYMENT_DECLINE_TOKEN` environment setting instead of a hardcoded value.

4. **Idempotency key normalization:** Consistent case-insensitive and whitespace-insensitive key handling has not yet been verified through checkout retry tests.

## Verification

Commands run:

```bash
## Verification

Commands run:

```bash
python -m scripts.reset_db
python -m scripts.seed
uvicorn app.main:app --reload
pytest -v# e.g. pytest
```

Visible suite result:

Pending — automated tests have not yet been executed. No passing or failing test count is currently available.

Before/after reproduction for each fixed defect:

## Checklist

## Checklist

- [x] I have read `docs/requirements.md` and `docs/submission.md`
- [ ] No changes to `tests/` or `docs/requirements.md`
- [ ] A clean checkout runs using the steps in the README
- [ ] Retry and decline behavior matches `docs/requirements.md`
- [ ] Every item in the bug inventory is fixed or listed under "Defects not fixed"
- [ ] No database files, secrets, or generated artifacts are committed
- [x] I understand this PR is evaluated once, when opened, and will not be merged
