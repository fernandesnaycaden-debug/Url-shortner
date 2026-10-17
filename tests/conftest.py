import pytest

from app import create_app


@pytest.fixture
def app():
    # In-memory SQLite: every test gets a fresh, empty database.
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})


@pytest.fixture
def client(app):
    return app.test_client()
