import pytest
import uuid
from rich.console import Console

from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_repetition import RepetitionTodo
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository


@pytest.mark.parametrize("state, has_parent, expected_to_repeat", [
    (False, False, False),  # Cas 1 : Non terminée -> None
    (True,  True,  False),  # Cas 2 : Terminée mais Enfant -> None
    (True,  False, True),   # Cas 3 : Racine terminée -> list(Todo)
])
def test_repetition_rule_1_logic(user_id, state, has_parent, expected_to_repeat):
    # GIVEN
    repo = MemoryTodoRepository()
    parent_id = uuid.uuid4() if has_parent else None
    
    todo = Todo(
        title="Test Task",
        user=user_id,
        state=state,
        parent=parent_id,
        frequency="daily"
    )
    repo.save(todo)
    
    # WHEN
    use_case = RepetitionTodo(repo)
    result = use_case.execute(todo.uuid)
    
    # EXPECTED
    if expected_to_repeat:
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], Todo)
        # Vérification de l'effet de bord
        assert len(repo.todos) == 2
    else:
        assert result is None
        # Vérification qu'aucune tâche n'a été créée
        assert len(repo.todos) == 1
