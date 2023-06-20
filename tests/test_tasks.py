from random import randint

import pytest

from src.dtos import dto_tasks


@pytest.mark.parametrize(
    "title, description",
    [
        ("new title 1", "new description 1"),
        ("new title 2", "new description 2"),
        ("new title 3", "new description 3"),
    ],
)
def test_create_tasks(
    authorized_client,
    test_user,
    title,
    description,
):
    response = authorized_client.post(
        f'{"/tasks/"}', json={"title": title, "description": description}
    )
    json = response.json()
    print(json)
    task = json["data"]["task"]
    print(response.json())
    created_post = dto_tasks.TaskResponse(**task)
    assert response.status_code == 201
    assert created_post.title == title
    assert created_post.description == description
    assert created_post.user_id == test_user.id


def test_create_max_tasks(
    authorized_client,
    test_user,
):
    existing_titles = set()
    for i in range(50):
        title = f"new title {i}"
        while title in existing_titles:
            title = f"new title {i} ({randint(0, 100)})"
        description = f"new description {i}"
        existing_titles.add(title)

        response = authorized_client.post(
            f'{"/tasks/"}', json={"title": title, "description": description}
        )
        assert response.status_code == 201
    title = "desired title"
    description = "desired description"
    response = authorized_client.post(
        f'{"/tasks/"}', json={"title": title, "description": description}
    )
    assert response.status_code == 403


def test_update_task(authorized_client, test_user, test_task):
    response = authorized_client.put(
        f"/tasks/{test_task[0].id}", json={"title": "new title"}
    )
    json = response.json()
    task = json["data"]["task"]
    assert response.status_code == 200
    updated_task = dto_tasks.TaskResponse(**task)
    assert updated_task.title == "new title"
    assert updated_task.user_id == test_user.id


def test_delete_task(authorized_client, test_task):
    response = authorized_client.delete(f"/tasks/{test_task[0].id}")
    assert response.status_code == 204


def test_get_tasks(authorized_client, test_task):
    response = authorized_client.get(f'{"/tasks/"}')
    assert response.status_code == 200
