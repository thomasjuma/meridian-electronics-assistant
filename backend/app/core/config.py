import os


class Settings:
    app_name: str = "OMS API"
    debug: bool = True

    def __init__(self) -> None:
        self.auth_jwt_secret_key = self._load_auth_jwt_secret_key()

    @staticmethod
    def _load_auth_jwt_secret_key() -> str:
        key = os.environ.get("AUTH_JWT_SECRET_KEY", "default_secret_key")
        return key


settings = Settings()
