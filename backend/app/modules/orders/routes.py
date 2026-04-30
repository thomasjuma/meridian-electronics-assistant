from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from . import service, schemas, repository
from .service import InvalidOrderTransition
from app.core.auth import get_current_user

router = APIRouter()


def get_orders_repository(db: Session = Depends(get_db)):
    return repository.OrderRepository(db)


@router.post("/", response_model=schemas.OrderRead)
def create_order(
    payload: schemas.OrderCreate,
    repo: repository.OrderRepository = Depends(get_orders_repository),
    _user: str = Depends(get_current_user),
):
    return service.create_order(repo, payload.item)


@router.get("/{order_id}", response_model=schemas.OrderRead)
def get_order(
    order_id: int,
    repo: repository.OrderRepository = Depends(get_orders_repository),
    _user: str = Depends(get_current_user),
):
    try:
        return service.get_order(repo, order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")


@router.get("/", response_model=list[schemas.OrderRead])
def list_orders(
    repo: repository.OrderRepository = Depends(get_orders_repository),
    _user: str = Depends(get_current_user),
):
    return service.list_orders(repo)


@router.put("/{order_id}", response_model=schemas.OrderRead)
def update_order(
    order_id: int,
    payload: schemas.OrderUpdate,
    repo: repository.OrderRepository = Depends(get_orders_repository),
    _user: str = Depends(get_current_user),
):
    try:
        updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
        return service.update_order(repo, order_id, **updates)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")
    except InvalidOrderTransition as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    repo: repository.OrderRepository = Depends(get_orders_repository),
    _user: str = Depends(get_current_user),
):
    try:
        service.delete_order(repo, order_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Order not found")
