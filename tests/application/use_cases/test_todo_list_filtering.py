import pytest
import pendulum
from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_find_top_level_by_user import TodoGetAllRootsByUserUseCase
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository

@pytest.fixture
def setup_filter_test():
    repository = MemoryTodoRepository()
    use_case = TodoGetAllRootsByUserUseCase(repository)
    user_id = uuid4()
    
    # 1. Un Todo pour AUJOURD'HUI
    todo_today = Todo(
        uuid=uuid4(),
        title="Task Today",
        date_start=pendulum.now().timestamp(),
        date_due=pendulum.now().at(23, 59, 59).timestamp(),
        user=user_id
    )
    
    # 2. Un Todo pour la SEMAINE PROCHAINE (hors mois si fin de mois)
    # On le place à +10 jours pour être sûr qu'il soit hors 'today' et 'week'
    todo_future = Todo(
        uuid=uuid4(),
        title="Task Future",
        date_start=pendulum.now().add(days=10).timestamp(),
        date_due=pendulum.now().add(days=10).at(23, 59, 59).timestamp(),
        user=user_id
    )
    
    repository.save(todo_today)
    repository.save(todo_future)
    
    return use_case, user_id, todo_today, todo_future

def test_execute_filter_today(setup_filter_test):
    use_case, user_id, todo_today, _ = setup_filter_test
    
    # Ce test va échouer car 'period' n'est pas encore accepté par execute()
    roots, count = use_case.execute(user_id, period="today")
    
    assert len(roots) == 1
    assert roots[0].title == "Task Today"

def test_execute_filter_all(setup_filter_test):
    use_case, user_id, _, _ = setup_filter_test
    
    # 'all' devrait retourner les deux tâches
    roots, count = use_case.execute(user_id, period="all")
    
    assert len(roots) == 2

def test_execute_filter_week(setup_filter_test):
    use_case, user_id, todo_today, _ = setup_filter_test
    repository = use_case.todo_repo
    
    # On ajoute une tâche à J+3 (normalement dans la semaine, sauf si on est dimanche)
    # Mais pour le test, on va la caler explicitement à la fin de la semaine actuelle
    end_of_week = pendulum.now().end_of('week').int_timestamp
    todo_week = Todo(
        uuid=uuid4(),
        title="Task Week",
        date_start=end_of_week - 3600,
        date_due=end_of_week,
        user=user_id
    )
    repository.save(todo_week)
    
    roots, count = use_case.execute(user_id, period="week")
    
    # Doit contenir Today + Week
    assert len(roots) == 2
    titles = [t.title for t in roots]
    assert "Task Today" in titles
    assert "Task Week" in titles

def test_execute_filter_month(setup_filter_test):
    use_case, user_id, _, _ = setup_filter_test
    repository = use_case.todo_repo
    
    # On ajoute une tâche à la fin du mois
    end_of_month = pendulum.now().end_of('month').int_timestamp
    todo_month = Todo(
        uuid=uuid4(),
        title="Task Month",
        date_start=end_of_month - 3600,
        date_due=end_of_month,
        user=user_id
    )
    repository.save(todo_month)
    
    roots, count = use_case.execute(user_id, period="month")
    
    # On s'attend à avoir au moins 3 tâches (Today + celle de la semaine + celle du mois)
    # Note : Le nombre exact dépend de si Task Future (J+10) tombe dans le mois ou pas
    assert any(t.title == "Task Month" for t in roots)