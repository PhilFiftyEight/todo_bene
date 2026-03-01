import pytest
import uuid
from todo_bene.domain.entities.todo import Todo
from todo_bene.domain.services.mail_engine import filter_todos_for_job

@pytest.fixture
def sample_todos(user_id):
    u = user_id
    return [
        Todo(uuid=uuid.uuid4(), user=u, title="Task A", category="Work", state=False, date_due=0),
        Todo(uuid=uuid.uuid4(), user=u, title="Task B", category="Home", state=False, date_due=0),
        Todo(uuid=uuid.uuid4(), user=u, title="Done Task", category="Work", state=True, date_due=0),
        Todo(uuid=uuid.uuid4(), user=u, title="Task C", category="Urgent", state=False, date_due=0),
    ]

def test_filter_should_include_only_specified_categories(sample_todos):
    # On ne veut que le "Work"
    filtered = filter_todos_for_job(sample_todos, include_cats=["Work"], exclude_cats=[])
    
    assert len(filtered) == 1
    assert filtered[0].title == "Task A"
    assert filtered[0].state is False

def test_filter_should_exclude_specified_categories(sample_todos):
    # On veut tout sauf "Urgent" (si include_cats est vide, on considère "tout" par défaut ou selon ta logique actuelle)
    # Note : Vérifie ta logique dans mail_engine.py, souvent si include est vide = tout.
    filtered = filter_todos_for_job(sample_todos, include_cats=[], exclude_cats=["Urgent"])
    
    # Devrait rester Task A (Work) et Task B (Home). Done Task est exclue par le state.
    titles = [t.title for t in filtered]
    assert "Task A" in titles
    assert "Task B" in titles
    assert "Task C" not in titles

def test_filter_should_prioritize_exclude_over_include(sample_todos):
    # Si on inclut Work mais qu'on exclut Work, le résultat doit être vide
    filtered = filter_todos_for_job(sample_todos, include_cats=["Work"], exclude_cats=["Work"])
    assert len(filtered) == 0

def test_filter_should_never_include_completed_tasks(sample_todos):
    filtered = filter_todos_for_job(sample_todos, include_cats=["Work"], exclude_cats=[])
    titles = [t.title for t in filtered]
    assert "Done Task" not in titles