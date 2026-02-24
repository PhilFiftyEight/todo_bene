import pytest
from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_get import TodoGetUseCase
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository

def test_todo_get_use_case_returns_completed_count(user_id):
    repo = MemoryTodoRepository()
    use_case = TodoGetUseCase(repo)
    
    # 1. Setup de la chaîne : Parent > B (Terminé) > C (En cours) > D (Terminé)
    todo_a = Todo(title="Parent", user=user_id)
    repo.save(todo_a)
    
    # B est terminé
    todo_b = Todo(title="Enfant", user=user_id, parent=todo_a.uuid, state=True)
    repo.save(todo_b)
    
    # C est en cours
    todo_c = Todo(title="Petit-Enfant", user=user_id, parent=todo_b.uuid)
    repo.save(todo_c)
    
    # D est terminé
    todo_d = Todo(title="Arriere-Petit-Enfant", user=user_id, parent=todo_c.uuid, state=True)
    repo.save(todo_d)

    # 2. Exécution : On s'attend à recevoir 4 valeurs
    # todo, children, total_count, completed_count
    result = use_case.execute(todo_a.uuid, user_id)
    
    # 3. Assertions (Va échouer ici : ValueError: too many values to unpack (expected 4))
    todo, children, total, completed = result
    
    assert total == 3     # B, C, D
    assert completed == 2  # B et D