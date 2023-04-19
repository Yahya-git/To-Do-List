import pytest
from jose import jwt

from src.config import settings
from src.dtos import dto_misc, dto_users


def test_root(client):
    response = client.get("/")
    assert response.json().get("message") == "Testing"
    assert response.status_code == 200


def test_create_user(client):
    response = client.post(
        "/users/", json={"email": "yahya.todolist@gmail.com", "password": "hello"}
    )
    json = response.json()
    user = json["data"]["user"]
    new_user = dto_users.UserResponse(**user)
    assert new_user.email == "yahya.todolist@gmail.com"
    assert response.status_code == 201


def test_update_user(authorized_client, test_user):
    response = authorized_client.put(
        f"/users/{test_user.id}/",
        json={
            "email": "yahya.todolist@gmail.com",
            "password": "hello",
            "first_name": "hello",
            "last_name": "world",
        },
    )
    json = response.json()
    user = json["data"]["user"]
    new_user = dto_users.UserResponse(**user)
    assert new_user.email == "yahya.todolist@gmail.com"
    assert response.status_code == 200


def test_wrong_update(client, test_user):
    response = client.put(
        f"/users/{test_user.id}/",
        json={
            "email": "hello@gmail.com",
            "password": "hello",
            "first_name": "hello",
            "last_name": "world",
        },
    )
    assert response.status_code == 401


def test_login_user(client, test_user_login):
    response = client.post(
        "/login",
        data={"username": test_user_login.email, "password": test_user_login.password},
    )
    print(response.json())
    login_res = dto_misc.TokenResponse(**response.json())
    decoded_jwt = jwt.decode(
        login_res.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    email: str = decoded_jwt.get("user_email")
    assert email == test_user_login.email
    assert login_res.token_type == "bearer"
    assert response.status_code == 202


@pytest.mark.parametrize(
    "email, password, status_code", [("wrongemail@gmail.com", "passwordwrong", 401)]
)
def test_wrong_login(client, email, password, status_code):
    response = client.post("/login", data={"username": email, "password": password})
    assert response.status_code == status_code
    assert response.json().get("detail") == "invalid credentials"
