import pytest
import uuid

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

@pytest.mark.parametrize("state, has_parent, num_children, expected_total_created", [
    (False, False, 0, 0),  # Cas 1 : Non terminée -> 0
    (True,  True,  0, 0),  # Cas 2 : Terminée & enfant-> 0
    (True,  False, 0, 1),  # Cas 3 : Terminée Racine seule -> 1
    (True,  False, 2, 3),  # Cas 4 : Terminée Racine + 2 enfants -> 3 (La racine + ses 2 petits)
])
def test_repetition_logic_with_children(user_id, state, has_parent, num_children, expected_total_created):
    # GIVEN
    repo = MemoryTodoRepository()
    parent_id = uuid.uuid4() if has_parent else None
    
    # Création de la tâche cible
    todo = Todo(
        title="Main Task",
        user=user_id,
        state=state,
        parent=parent_id,
        frequency="daily"
    )
    repo.save(todo)

    # Création des enfants si nécessaire
    for i in range(num_children):
        child = Todo(
            title=f"Child {i}",
            user=user_id,
            parent=todo.uuid  # Lié à notre tâche cible
        )
        repo.save(child)
    
    initial_repo_size = len(repo.todos)
    
    # WHEN
    use_case = RepetitionTodo(repo)
    result = use_case.execute(todo.uuid)
    
    # EXPECTED
    if expected_total_created > 0:
        assert isinstance(result, list)
        assert len(result) == expected_total_created
        assert len(repo.todos) == initial_repo_size + expected_total_created
    else:
        assert result is None

@pytest.mark.parametrize("description, structure_type, expected_total", [
    # 1. Linear: Root > C1 > GC1
    ("3-level linear", "linear", 3), 
    
    # 2. Asymmetric: Root > C1 / Root > C2 > GC2
    ("2 unequal branches", "asymmetric_2", 4),
    
    # 3. Complex: 4 branches with varying depths (up to 4 levels)
    ("Complex 4-branch structure", "complex_4", 9),
])
def test_repetition_deep_structures(user_id, description, structure_type, expected_total):
    # GIVEN
    repo = MemoryTodoRepository()
    root = Todo(title="Root", user=user_id, state=True, frequency="daily")
    repo.save(root)

    if structure_type == "linear":
        c1 = Todo(title="C1", user=user_id, parent=root.uuid)
        repo.save(c1)
        repo.save(Todo(title="GC1", user=user_id, parent=c1.uuid))

    elif structure_type == "asymmetric_2":
        repo.save(Todo(title="C1", user=user_id, parent=root.uuid))
        c2 = Todo(title="C2", user=user_id, parent=root.uuid)
        repo.save(c2)
        repo.save(Todo(title="GC2", user=user_id, parent=c2.uuid))

    elif structure_type == "complex_4":
        # Branch 1
        c1 = Todo(title="C1", user=user_id, parent=root.uuid)
        repo.save(c1)
        repo.save(Todo(title="GC1", user=user_id, parent=c1.uuid))
        
        # Branch 2
        repo.save(Todo(title="C2", user=user_id, parent=root.uuid))
        
        # Branch 3
        c3 = Todo(title="C3", user=user_id, parent=root.uuid)
        repo.save(c3)
        repo.save(Todo(title="GC3", user=user_id, parent=c3.uuid))
        
        # Branch 4
        c4 = Todo(title="C4", user=user_id, parent=root.uuid)
        repo.save(c4)
        gc4 = Todo(title="GC4", user=user_id, parent=c4.uuid)
        repo.save(gc4)
        repo.save(Todo(title="GGC4", user=user_id, parent=gc4.uuid))

    # WHEN
    use_case = RepetitionTodo(repo)
    result = use_case.execute(root.uuid)

    # EXPECTED
    assert len(result) == expected_total