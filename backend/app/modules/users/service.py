from . import repository, schemas
from fastapi import HTTPException, status


def create_user(repo: repository.UserRepository, username: str, password: str):
    existing_user = repo.get_user_by_username(username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    return repo.create_user(username, password)


def authenticate_user(repo: repository.UserRepository, username: str, password: str):
    user = repo.get_user_by_username(username)
    if not user or not repo.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
