import pytest
import uuid
import pendulum
from rich.console import Console

from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_repetition import RepetitionTodo
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository

@pytest.fixture
def test_date():
    tz = pendulum.local_timezone()
    date = pendulum.now(tz=tz).add(days=1)
    return date.format("YYYY-MM-DD")


@pytest.mark.parametrize("state, has_parent, expected_to_repeat", [
    (False, False, False),  # Cas 1 : Non terminée -> None
    (True,  True,  False),  # Cas 2 : Terminée mais Enfant -> None
    (True,  False, True),   # Cas 3 : Racine terminée -> list(Todo)
])
def test_repetition_rule_1_logic(test_date, user_id, state, has_parent, expected_to_repeat):
    # GIVEN
    repo = MemoryTodoRepository()
    parent_id = uuid.uuid4() if has_parent else None
    
    todo = Todo(
        title="Test Task",
        user=user_id,
        state=state,
        parent=parent_id,
        frequency=test_date
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
def test_repetition_logic_with_children(test_date,user_id, state, has_parent, num_children, expected_total_created):
    # GIVEN
    repo = MemoryTodoRepository()
    parent_id = uuid.uuid4() if has_parent else None
    
    # Création de la tâche cible
    todo = Todo(
        title="Main Task",
        user=user_id,
        state=state,
        parent=parent_id,
        frequency=test_date
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
def test_repetition_deep_structures(test_date,user_id, description, structure_type, expected_total):
    # GIVEN
    repo = MemoryTodoRepository()
    root = Todo(title="Root", user=user_id, state=True, frequency=test_date)
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

@pytest.mark.parametrize("description, requested_start, expected_days_delta", [
    # 1. Immediate Shift: User validates empty, CLI sends 'tomorrow'
    ("Immediate shift to tomorrow", 
     "tomorrow", 
     1),
    
    # 2. Explicit Shift: Specific date (3 days from now)
    ("Explicit shift to 3 days later", 
     pendulum.now(tz=pendulum.local_timezone()).add(days=3).to_date_string(), 
     3),
    
    # 3. Frequency-based Shift: (e.g., 'next week' -> +7 days)
    ("Explicit shift to next week", 
     pendulum.now(tz=pendulum.local_timezone()).add(weeks=1).to_date_string(), 
     7),
])
def test_repetition_tomorrow_frequency(user_id, description, requested_start, expected_days_delta):
    """
    Test Rule 3: A frequency of 'tomorrow' should shift the entire tree 
    by one day compared to the original start date.
    """
    # GIVEN
    repo = MemoryTodoRepository()
    tz = pendulum.local_timezone()
    
    # Original root task
    now = pendulum.now(tz=tz)
    # We define a specific duration for the root (e.g., from now until end of day)
    root = Todo(
        title="Root", 
        user=user_id, 
        state=True, 
        frequency=requested_start,
        date_start=now.int_timestamp
    )
    repo.save(root)
    
    # Child task: starts 2 hours after parent root
    child_start = now.add(hours=2).int_timestamp
    repo.save(Todo(
        title="Child", 
        user=user_id, 
        parent=root.uuid,
        date_start=child_start
    ))

    # WHEN
    use_case = RepetitionTodo(repo)
    # Note: No new_start_date here, we use the frequency field of the object
    result = use_case.execute(root.uuid)

    # EXPECTED
    assert result is not None
    new_root = next(t for t in result if t.parent is None)
    new_child = next(t for t in result if t.parent == new_root.uuid)

    # 1. Check Root Start: Must be exactly the original start + 1 day
    expected_root_start = pendulum.from_timestamp(root.date_start, tz=tz).add(days=expected_days_delta).int_timestamp
    assert new_root.date_start == expected_root_start
    
    
    # 2. Check Duration Preservation: date_due - date_start must remain identical
    original_duration = root.date_due - root.date_start
    new_duration = new_root.date_due - new_root.date_start
    assert new_duration == original_duration

    # 3. Check Child Shift: Must remain exactly 2 hours after the NEW parent
    expected_child_start = pendulum.from_timestamp(new_root.date_start, tz=tz).add(hours=2).int_timestamp
    assert new_child.date_start == expected_child_start

def test_repetition_duration_integrity(test_date, user_id):
    """
    Vérifie que la durée (due - start) est préservée à la seconde près
    pour la racine et ses descendants après répétition.
    """
    # GIVEN
    repo = MemoryTodoRepository()
    tz = pendulum.local_timezone()
    now = pendulum.now(tz=tz)

    # 1. Racine : durée de 3 heures
    root_start = now.int_timestamp
    root_due = now.add(hours=3).int_timestamp
    root = Todo(
        title="Root 3h", 
        user=user_id, 
        state=True, 
        frequency=test_date,
        date_start=root_start,
        date_due=root_due
    )
    repo.save(root)

    # 2. Enfant : durée de 45 minutes
    child_start = now.add(hours=1).int_timestamp
    child_due = now.add(hours=1, minutes=45).int_timestamp
    child = Todo(
        title="Child 45m", 
        user=user_id, 
        parent=root.uuid,
        date_start=child_start,
        date_due=child_due
    )
    repo.save(child)

    # WHEN
    use_case = RepetitionTodo(repo)
    result = use_case.execute(root.uuid)

    # EXPECTED
    new_root = next(t for t in result if t.parent is None)
    new_child = next(t for t in result if t.parent == new_root.uuid)

    # Vérification Racine
    original_root_duration = root_due - root_start
    new_root_duration = new_root.date_due - new_root.date_start
    assert new_root_duration == original_root_duration
    assert new_root_duration == 10800  # 3 * 3600 secondes

    # Vérification Enfant
    original_child_duration = child_due - child_start
    new_child_duration = new_child.date_due - new_child.date_start
    assert new_child_duration == original_child_duration
    assert new_child_duration == 2700  # 45 * 60 secondes