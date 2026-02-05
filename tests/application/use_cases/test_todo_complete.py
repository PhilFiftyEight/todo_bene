import pytest  # noqa: F401
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_complete import TodoCompleteUseCase
from todo_bene.infrastructure.persistence.memory_todo_repository import (
    MemoryTodoRepository,
)


def test_todo_complete_simple(user_id):
    # GIVEN : Un utilisateur et une tâche non terminée
    repo = MemoryTodoRepository()
    todo = Todo(title="Acheter du pain", user=user_id)
    repo.save(todo)

    # On s'assure qu'elle est bien à 'False' au début
    assert todo.state is False

    use_case = TodoCompleteUseCase(repo)

    # WHEN : On demande au Use Case de la compléter
    use_case.execute(todo_id=todo.uuid, user_id=user_id)

    # THEN : On vérifie en base que l'état est passé à True
    updated_todo = repo.get_by_id(todo.uuid)
    assert updated_todo.state is True
