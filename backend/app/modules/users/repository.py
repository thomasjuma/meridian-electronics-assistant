import bcrypt
import hashlib
from sqlalchemy.orm import Session
from . import models


class UserRepository:
    def __init__(self, db: Session):
        self._db = db

    def create_user(self, username: str, password: str):
        hashed_password = self._hash_password(password)
        user = models.User(username=username, hashed_password=hashed_password)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_user_by_username(self, username: str):
        return self._db.query(models.User).filter(models.User.username == username).first()

    def get_user_by_id(self, user_id: int):
        return self._db.query(models.User).filter(models.User.id == user_id).first()

    def _hash_password(self, password: str) -> str:
        if len(password) > 72:
            password = hashlib.sha256(password.encode()).hexdigest()
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if len(plain_password) > 72:
            plain_password = hashlib.sha256(plain_password.encode()).hexdigest()
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return UserRepository.verify_password(plain_password, hashed_password)
