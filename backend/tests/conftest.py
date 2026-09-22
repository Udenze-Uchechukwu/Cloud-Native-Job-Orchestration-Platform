import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.main import app


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    # create_savepoint mode: the app's db.commit() calls (inside endpoints) only
    # release a SAVEPOINT rather than the outer transaction, so everything the
    # test did is still rolled back here, keeping tests isolated from each other.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
