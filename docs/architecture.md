# Architecture

FastAPI routes validate request and response shapes through Pydantic. SQLAlchemy owns the product, cart, order, and payment-attempt models. `order_service` coordinates pricing, inventory reservation, and the fake payment provider in one database transaction. A checkout key is persisted with the order and is intended to make retries return the original result.

Prices are integer minor units. Inventory is checked before reservation. A declined payment returns HTTP 402 and does not create an order.

The local database is created on application import, while seed data is explicit and repeatable.
