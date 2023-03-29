import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import models
from app.database.database import Base, get_db
from app.main import app
from app.schemas import schemas_users

SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{settings.db_username}:{settings.db_password}@{settings.db_hostname}:{settings.db_port}/{settings.db_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def test_user(client):
    user_data = {"email": "yahya.19of99@gmail.com", "password": "hello"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    user = response.json()
    user["password"] = user_data["password"]
    return schemas_users.User(**user)


@pytest.fixture
def test_user_update(client):
    user_data = {"email": "yahya.19of99@gmail.com", "password": "hello"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    user = response.json()
    user["password"] = user_data["password"]
    return schemas_users.User(**user)


@pytest.fixture
def test_user_login(client, session):
    user_data = {"email": "yahya.19of99@gmail.com", "password": "hello"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    user = response.json()
    session.query(models.User).filter(models.User.email == user_data["email"]).update(
        {"is_verified": True}
    )
    session.commit()
    user["password"] = user_data["password"]
    return schemas_users.UserCreate(**user)
