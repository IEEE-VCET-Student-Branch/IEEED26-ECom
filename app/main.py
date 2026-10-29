from fastapi import FastAPI
from .api import cart, checkout, health, orders, products
from .database import init_db

app = FastAPI(title="Northstar Market", version="1.0.0")
app.include_router(health.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
init_db()
