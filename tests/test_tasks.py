import pytest

from app.dtos import dto_tasks


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
    res = authorized_client.post(
        f'{"/tasks/"}', json={"title": title, "description": description}
    )
    print(res.json())
    created_post = dto_tasks.TaskResponse(**res.json())
    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.description == description
    assert created_post.user_id == test_user.id


def test_update_task(authorized_client, test_user, test_task):
    res = authorized_client.patch(
        f"/tasks/{test_task[0].id}", json={"title": "new title"}
    )
    assert res.status_code == 202
    updated_task = dto_tasks.TaskResponse(**res.json())
    assert updated_task.title == "new title"
    assert updated_task.user_id == test_user.id


def test_delete_task(authorized_client, test_task):
    res = authorized_client.delete(f"/tasks/{test_task[0].id}")
    assert res.status_code == 204
