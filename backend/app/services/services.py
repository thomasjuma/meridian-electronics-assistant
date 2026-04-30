from repository import OrderRepository
from models import OrderStatus


class InvalidOrderTransition(Exception):
    """Raised when a requested status transition is not allowed."""
    pass


class OrderStateMachine:
    """Finite state machine for order status transitions."""

    TRANSITIONS = {
            OrderStatus.RECEIVED: [
            OrderStatus.PROCESSING,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.PROCESSING: [
                OrderStatus.FULFILLED,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.FULFILLED: [
            OrderStatus.SHIPPED,
            OrderStatus.CANCELLED,
        ],
        OrderStatus.SHIPPED: [
            OrderStatus.DELIVERED
        ],
        OrderStatus.DELIVERED: [],
        OrderStatus.CANCELLED: [],
    }

    @classmethod
    def validate_transition(cls, current: OrderStatus, target: OrderStatus) -> None:
        allowed = cls.TRANSITIONS.get(current)
        if allowed is None:
            raise InvalidOrderTransition(f"Unknown status: {current}")
        if target not in allowed:
            raise InvalidOrderTransition(
                f"Cannot transition from {current} to {target}"
            )


def create_order(repo: OrderRepository, item: str):
    return repo.create_order(item)


def get_order(repo: OrderRepository, order_id: int):
    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    return order


def list_orders(repo: OrderRepository):
    return repo.list_orders()


def update_order(repo: OrderRepository, order_id: int, **kwargs):
    """Update an order with the provided fields. Raises ValueError if not found."""
    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Order not found")

    if "status" in kwargs and kwargs["status"] is not None:
        OrderStateMachine.validate_transition(order.status, kwargs["status"])

    for key, value in kwargs.items():
        if value is not None:
            setattr(order, key, value)
    repo._db.commit()
    repo._db.refresh(order)
    return order


def delete_order(repo: OrderRepository, order_id: int):
    """Delete an order. Raises ValueError if not found."""
    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    repo._db.delete(order)
    repo._db.commit()
