import pytest  # noqa: F401
# from uuid import uuid4
from todo_bene.domain.entities.todo import Todo

def test_repository_save_and_get_by_id(repository, user_id):
    todo = Todo(title="Test Todo", user=user_id)
    repository.save(todo)
    
    retrieved = repository.get_by_id(todo.uuid)
    assert retrieved is not None
    assert retrieved.title == "Test Todo"
    assert retrieved.user == user_id

def test_repository_preserves_priority(repository, user_id):
    todo = Todo(title="Urgent", user=user_id, priority=True)
    repository.save(todo)
    
    retrieved = repository.get_by_id(todo.uuid)
    assert retrieved.priority is True

def test_repository_preserves_dates(repository, user_id):
    todo = Todo(title="Timed", user=user_id, date_start=1000, date_due=2000)
    repository.save(todo)
    
    retrieved = repository.get_by_id(todo.uuid)
    assert retrieved.date_start == 1000
    assert retrieved.date_due == 2000

def test_search_by_title_returns_matching_todos(repository, user_id):
    # GIVEN
    t1 = Todo(title="Acheter du pain", user=user_id, category="Courses")
    t2 = Todo(title="Acheter du lait", user=user_id, category="Courses")
    t3 = Todo(title="Nettoyer le salon", user=user_id, category="Maison")
    
    repository.save(t1)
    repository.save(t2)
    repository.save(t3)

    # WHEN
    results = repository.search_by_title(user_id, "Ach")

    # THEN
    assert len(results) == 2
    titles = [t.title for t in results]
    assert "Acheter du pain" in titles
    assert "Acheter du lait" in titles

def test_search_by_title_is_case_insensitive(repository, user_id):
    # GIVEN
    repository.save(Todo(title="Urgent : Rapport", user=user_id, category="Pro"))

    # WHEN
    results = repository.search_by_title(user_id, "urgent")

    # THEN
    assert len(results) == 1
    assert results[0].title == "Urgent : Rapport"

def test_repository_recursive_delete(repository, user_id):
    from todo_bene.domain.entities.todo import Todo
    
    parent = Todo(title="Parent", user=user_id)
    child = Todo(title="Enfant", user=user_id, parent=parent.uuid)
    grand_child = Todo(title="Petit-enfant", user=user_id, parent=child.uuid)
    
    repository.save(parent)
    repository.save(child)
    repository.save(grand_child)

    # Cette ligne va lever une AttributeError car .delete() n'existe pas encore dans DuckDB
    repository.delete(parent.uuid)

    assert repository.get_by_id(parent.uuid) is None
    assert repository.get_by_id(child.uuid) is None
    assert repository.get_by_id(grand_child.uuid) is None