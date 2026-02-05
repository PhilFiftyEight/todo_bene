import pendulum
import pytest

from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_update import TodoUpdateUseCase
from todo_bene.infrastructure.persistence.memory_todo_repository import (
    MemoryTodoRepository,
)


def test_todo_update_use_case_checks_parent_due_date(user_id):
    repo = MemoryTodoRepository()
    # Parent finit demain
    parent_due = pendulum.now().add(days=1).at(23, 59, 59).timestamp()
    parent = Todo(title="Parent", user=user_id, date_due=parent_due)
    repo.save(parent)

    # Enfant calé sur le parent
    child = Todo(title="Enfant", user=user_id, parent=parent.uuid, date_due=parent_due)
    repo.save(child)

    use_case = TodoUpdateUseCase(repo)

    # Tentative de mettre l'enfant à J+2 (après le parent)
    too_late = pendulum.now().add(days=2).timestamp()

    import pytest

    with pytest.raises(
        ValueError, match="L'échéance de l'enfant ne peut pas dépasser celle du parent"
    ):
        use_case.execute(todo_id=child.uuid, date_due=too_late)


def test_todo_update_use_case_refuses_category_change_for_child(user_id):
    # GIVEN
    repo = MemoryTodoRepository()
    parent = Todo(title="Parent", user=user_id, category="Travail")
    repo.save(parent)

    child = Todo(title="Enfant", user=user_id, parent=parent.uuid, category="Travail")
    repo.save(child)

    use_case = TodoUpdateUseCase(repo)

    # WHEN / THEN
    with pytest.raises(
        ValueError, match="La catégorie d'un enfant est verrouillée sur celle du parent"
    ):
        use_case.execute(todo_id=child.uuid, category="Personnel")
