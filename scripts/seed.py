from app.database import SessionLocal, init_db
from app.models import Product


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            db.add_all([
                Product(sku="NST-COFFEE", name="Northstar Coffee", description="Medium roast beans", price_minor=1299, inventory=20),
                Product(sku="NST-MUG", name="Enamel Camp Mug", description="A durable 12oz mug", price_minor=1899, inventory=15),
                Product(sku="NST-NOTEBOOK", name="Field Notebook", description="Dot-grid notebook", price_minor=799, inventory=50),
            ])
            db.commit()
    finally:
        db.close()


def catalog_size() -> int:
    db = SessionLocal()
    try:
        return db.query(Product).count()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
