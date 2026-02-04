import pytest
from uuid import uuid4
from todo_bene.application.use_cases.todo_delete import TodoDeleteUseCase
from todo_bene.infrastructure.persistence.memory_todo_repository import (
    MemoryTodoRepository,
)
from todo_bene.domain.entities.todo import Todo


def test_todo_delete_use_case_success(user_id):
    # GIVEN
    repo = MemoryTodoRepository()
    use_case = TodoDeleteUseCase(repo)
    todo = Todo(title="À supprimer", user=user_id)
    repo.save(todo)

    # WHEN
    use_case.execute(todo_id=todo.uuid, user_id=user_id)

    # THEN
    assert repo.get_by_id(todo.uuid) is None


def test_todo_delete_fails_for_wrong_user():
    # GIVEN
    repo = MemoryTodoRepository()
    use_case = TodoDeleteUseCase(repo)
    owner_id = uuid4()
    stranger_id = uuid4()

    todo = Todo(title="Pas à toi", user=owner_id)
    repo.save(todo)

    # WHEN / THEN
    with pytest.raises(ValueError, match="Vous n'avez pas l'autorisation"):
        use_case.execute(todo_id=todo.uuid, user_id=stranger_id)

    # La tâche ne doit pas avoir été supprimée
    assert repo.get_by_id(todo.uuid) is not None
