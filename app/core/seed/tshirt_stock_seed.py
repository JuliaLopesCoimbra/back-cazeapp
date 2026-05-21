from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.admin.models.tshirt_stock_item_model import TshirtStockItem

DEFAULT_ROWS = [
    ("PP", 1364),
    ("P", 2500),
    ("M", 3409),
    ("G", 1818),
    ("GG", 591),
    ("EXG", 318),
]


def seed_tshirt_stock_if_empty(db: Session) -> None:
    count = db.query(TshirtStockItem).count()
    if count > 0:
        return
    for size, qty in DEFAULT_ROWS:
        db.add(TshirtStockItem(size=size, quantity=qty, created_at=datetime.utcnow()))
    db.commit()
    print("✅ Estoque inicial de camisetas criado (6 tamanhos).")
