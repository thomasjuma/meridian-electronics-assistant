from . import repository, models


class InvalidOrderTransition(Exception):
    """Raised when a requested status transition is not allowed."""
    pass


class OrderStateMachine:
    """Finite state machine for order status transitions."""

    TRANSITIONS = {
        models.OrderStatus.RECEIVED: [
            models.OrderStatus.PROCESSING,
            models.OrderStatus.CANCELLED,
        ],
        models.OrderStatus.PROCESSING: [
            models.OrderStatus.FULFILLED,
            models.OrderStatus.CANCELLED,
        ],
        models.OrderStatus.FULFILLED: [
            models.OrderStatus.SHIPPED,
            models.OrderStatus.CANCELLED,
        ],
        models.OrderStatus.SHIPPED: [
            models.OrderStatus.DELIVERED
        ],
        models.OrderStatus.DELIVERED: [],
        models.OrderStatus.CANCELLED: [],
    }

    @classmethod
    def validate_transition(cls, current: models.OrderStatus, target: models.OrderStatus) -> None:
        allowed = cls.TRANSITIONS.get(current)
        if allowed is None:
            raise InvalidOrderTransition(f"Unknown status: {current}")
        if target not in allowed:
            raise InvalidOrderTransition(
                f"Cannot transition from {current} to {target}"
            )


def create_order(repo: repository.OrderRepository, item: str):
    return repo.create_order(item)


def get_order(repo: repository.OrderRepository, order_id: int):
    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    return order


def list_orders(repo: repository.OrderRepository):
    return repo.list_orders()


def update_order(repo: repository.OrderRepository, order_id: int, **kwargs):
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


def delete_order(repo: repository.OrderRepository, order_id: int):
    """Delete an order. Raises ValueError if not found."""
    order = repo.get_order(order_id)
    if not order:
        raise ValueError("Order not found")
    repo._db.delete(order)
    repo._db.commit()
