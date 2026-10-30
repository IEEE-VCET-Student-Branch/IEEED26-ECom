# THE FINAL COMMIT: Northstar Market

Northstar Market is a small FastAPI e-commerce service prepared for **THE FINAL COMMIT**, a source-and-history debugging competition. It is intentionally supplied with regressions. Participants should investigate the code, tests, and Git history rather than assume the incident documents are authoritative.

The behavioral contract the service must satisfy is in [`docs/requirements.md`](docs/requirements.md). Submission rules are in [`docs/submission.md`](docs/submission.md).

## Run Locally

### Prerequisites

- Python 3.11
- pip

### 1. Create a virtual environment

**Windows (PowerShell):**

```powershell
py -3.11 -m venv .venv
```

**Linux/macOS:**

```bash
python3.11 -m venv .venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the database

```bash
python -m scripts.reset_db
python -m scripts.seed
```

### 5. Start the server

```bash
uvicorn app.main:app --reload
```

Open the API documentation at:

http://127.0.0.1:8000/docs

**Note:** The seed command is safe to run repeatedly. It inserts the deterministic catalogue only when the database contains no products.

## Tests

```bash
pytest
```

The test suite covers ordinary behavior but is deliberately not a complete incident specification. The API has products, carts, checkout, orders, inventory validation, deterministic pricing, a fake payment provider, and an idempotency header on checkout. `docs/requirements.md` is the authoritative contract; the visible tests cover only part of it.

## Useful API sequence

1. `GET /products`
2. `POST /cart/{customer_id}/items` with `{"product_id": 1, "quantity": 1}`
3. `POST /checkout` with an `Idempotency-Key` header and `{"customer_id": "...", "payment_token": "tok"}`
4. `GET /orders/{order_id}`

The `docs/` and `fixtures/` folders contain the contemporaneous project evidence available to participants.

No external database or payment account is needed.
