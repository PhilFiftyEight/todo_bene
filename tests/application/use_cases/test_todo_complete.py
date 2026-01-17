import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_complete import TodoCompleteUseCase


def test_todo_complete_simple(repository):
    # GIVEN : Un utilisateur et une tâche non terminée
    user_id = uuid4()
    todo = Todo(title="Acheter du pain", user=user_id)
    repository.save(todo)

    # On s'assure qu'elle est bien à 'False' au début
    assert todo.state is False

    use_case = TodoCompleteUseCase(repository)

    # WHEN : On demande au Use Case de la compléter
    use_case.execute(todo_id=todo.uuid, user_id=user_id)

    # THEN : On vérifie en base que l'état est passé à True
    updated_todo = repository.get_by_id(todo.uuid)
    assert updated_todo.state is True
