from sqlalchemy.orm import Session
from . import models


class OrderRepository:
    def __init__(self, db: Session):
        self._db = db

    def create_order(self, item: str):
        order = models.Order(item=item)
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def get_order(self, order_id: int):
        return self._db.query(models.Order).filter(models.Order.id == order_id).first()

    def list_orders(self):
        return self._db.query(models.Order).all()

    def update_order(self, order_id: int, **kwargs):
        order = self._db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        for field, value in kwargs.items():
            if value is not None:
                setattr(order, field, value)
        self._db.commit()
        self._db.refresh(order)
        return order

    def delete_order(self, order_id: int):
        order = self._db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise ValueError("Order not found")
        self._db.delete(order)
        self._db.commit()
        return True
