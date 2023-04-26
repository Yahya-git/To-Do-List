import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database import Base, get_db
from src.dtos import dto_users
from src.handler.utils import create_access_token
from src.main import app
from src.models import tasks, users

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
def test_user_login(client, session):
    user_data = {"email": "yahya.19of99@gmail.com", "password": "hello"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    json = response.json()
    user = json["data"]["user"]
    session.query(users.User).filter(users.User.email == user_data["email"]).update(
        {"is_verified": True}
    )
    session.commit()
    user["password"] = user_data["password"]
    return dto_users.CreateUserRequest(**user)


@pytest.fixture
def test_user(client, session):
    user_data = {"email": "yahya.19of99@gmail.com", "password": "hello"}
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    json = response.json()
    user = json["data"]["user"]
    session.query(users.User).filter(users.User.email == user_data["email"]).update(
        {"is_verified": True}
    )
    session.commit()
    user["password"] = user_data["password"]
    return dto_users.UserResponse(**user)


@pytest.fixture
def token(test_user):
    return create_access_token({"user_email": test_user.email, "user_id": test_user.id})


@pytest.fixture
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def test_task(test_user, session):
    tasks_data = [
        {
            "title": "Test Task",
            "description": "Test Task Description",
            "user_id": test_user.id,
        }
    ]

    def create_task(task):
        return tasks.Task(**task)

    task_map = map(create_task, tasks_data)
    task = list(task_map)
    session.add_all(task)
    session.commit()
    taskslist = session.query(tasks.Task).all()
    return taskslist
