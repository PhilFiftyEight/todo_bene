import pytest  # noqa: F401
from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.get_pending_completion_parents import (
    GetPendingCompletionParentsUseCase,
)


def test_get_pending_completion_parents(repository):
    user_id = uuid4()
    use_case = GetPendingCompletionParentsUseCase(repository)

    # CAS 1 : Parent A - Tous les enfants sont complétés -> Doit être trouvé
    parent_a = Todo(title="Parent A", user=user_id)
    repository.save(parent_a)
    child_a1 = Todo(title="Enfant A1", user=user_id, parent=parent_a.uuid, state=True)
    repository.save(child_a1)

    # CAS 2 : Parent B - Un enfant sur deux complété -> Ne doit PAS être trouvé
    parent_b = Todo(title="Parent B", user=user_id)
    repository.save(parent_b)
    child_b1 = Todo(title="Enfant B1", user=user_id, parent=parent_b.uuid, state=True)
    child_b2 = Todo(title="Enfant B2", user=user_id, parent=parent_b.uuid, state=False)
    repository.save(child_b1)
    repository.save(child_b2)

    # CAS 3 : Parent C - Déjà complété -> Ne doit PAS être trouvé
    parent_c = Todo(title="Parent C", user=user_id, state=True)
    repository.save(parent_c)
    child_c1 = Todo(title="Enfant C1", user=user_id, parent=parent_c.uuid, state=True)
    repository.save(child_c1)

    # EXECUTION
    pending_parents = use_case.execute(user_id=user_id)

    # ASSERTIONS
    assert len(pending_parents) == 1
    assert pending_parents[0].uuid == parent_a.uuid
    assert pending_parents[0].title == "Parent A"
