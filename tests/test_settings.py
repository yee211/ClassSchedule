import pytest

from app.settings import Settings


def test_production_rejects_insecure_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="dev-insecure-secret-change-me").validate()


def test_development_accepts_local_defaults():
    Settings(environment="development").validate()
