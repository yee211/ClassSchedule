import pytest

from app.settings import Settings


def test_production_rejects_insecure_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        Settings(environment="production", jwt_secret="dev-insecure-secret-change-me").validate()


def test_development_accepts_local_defaults():
    Settings(environment="development").validate()


def test_production_rejects_implicit_demo_password(monkeypatch):
    monkeypatch.delenv("DEFAULT_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="默认演示账号密码"):
        Settings(environment="production", jwt_secret="x" * 32).validate()


def test_unknown_environment_is_rejected():
    with pytest.raises(RuntimeError, match="APP_ENV"):
        Settings(environment="prod", jwt_secret="x" * 32).validate()
