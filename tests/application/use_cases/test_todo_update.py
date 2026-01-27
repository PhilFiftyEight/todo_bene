from uuid import uuid4
import pendulum
import pytest

from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_update import TodoUpdateUseCase

def test_todo_update_use_case_checks_parent_due_date(repository):
    user_id = uuid4()
    # Parent finit demain
    parent_due = pendulum.now().add(days=1).at(23, 59, 59).timestamp()
    parent = Todo(title="Parent", user=user_id, date_due=parent_due)
    repository.save(parent)
    
    # Enfant calé sur le parent
    child = Todo(title="Enfant", user=user_id, parent=parent.uuid, date_due=parent_due)
    repository.save(child)
    
    use_case = TodoUpdateUseCase(repository)
    
    # Tentative de mettre l'enfant à J+2 (après le parent)
    too_late = pendulum.now().add(days=2).timestamp()
    
    import pytest
    with pytest.raises(ValueError, match="L'échéance de l'enfant ne peut pas dépasser celle du parent"):
        use_case.execute(todo_id=child.uuid, date_due=too_late)

def test_todo_update_use_case_refuses_category_change_for_child(repository):
    # GIVEN
    user_id = uuid4()
    parent = Todo(title="Parent", user=user_id, category="Travail")
    repository.save(parent)
    
    child = Todo(title="Enfant", user=user_id, parent=parent.uuid, category="Travail")
    repository.save(child)
    
    use_case = TodoUpdateUseCase(repository)
    
    # WHEN / THEN
    with pytest.raises(ValueError, match="La catégorie d'un enfant est verrouillée sur celle du parent"):
        use_case.execute(todo_id=child.uuid, category="Personnel")