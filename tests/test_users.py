import pytest
from jose import jwt

from app.config import settings
from app.schemas import schemas_misc, schemas_users


def test_root(client):
    res = client.get("/")
    assert res.json().get("message") == "Testing"
    assert res.status_code == 200


def test_create_user(client):
    res = client.post("/users/", json={"email": "hello@gmail.com", "password": "hello"})
    new_user = schemas_users.User(**res.json())
    assert new_user.email == "hello@gmail.com"
    assert res.status_code == 201


def test_update_user(client, test_user_update):
    res = client.patch(
        f"/users/{test_user_update.id}/",
        json={
            "email": "hello@gmail.com",
            "password": "hello",
            "first_name": "hello",
            "last_name": "world",
        },
    )
    new_user = schemas_users.User(**res.json())
    assert new_user.email == "hello@gmail.com"
    assert res.status_code == 202


def test_login_user(client, test_user_login):
    res = client.post(
        "/login",
        data={"username": test_user_login.email, "password": test_user_login.password},
    )
    print(res.json())
    login_res = schemas_misc.Token(**res.json())
    decoded_jwt = jwt.decode(
        login_res.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    email: str = decoded_jwt.get("user_email")
    assert email == test_user_login.email
    assert login_res.token_type == "bearer"
    assert res.status_code == 202


@pytest.mark.parametrize(
    "email, password, status_code", [("wrongemail@gmail.com", "passwordwrong", 403)]
)
def test_wrong_login(client, email, password, status_code):
    res = client.post("/login", data={"username": email, "password": password})
    assert res.status_code == status_code
    assert res.json().get("detail") == "invalid credentials"
