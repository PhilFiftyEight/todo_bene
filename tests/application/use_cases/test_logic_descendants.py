import pytest
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_get import TodoGetUseCase
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository

def test_recursive_count_long_chain(user_id):
    repo_memory = MemoryTodoRepository()
    use_case = TodoGetUseCase(repo_memory)
    # 1. Setup de la chaîne : A > B > C > D > E
    todo_a = Todo(title="Parent", user=user_id)
    repo_memory.save(todo_a)
    
    todo_b = Todo(title="Enfant", user=user_id, parent=todo_a.uuid)
    repo_memory.save(todo_b)
    
    todo_c = Todo(title="Petit-Enfant", user=user_id, parent=todo_b.uuid)
    repo_memory.save(todo_c)
    
    todo_d = Todo(title="Arrière-Petit-Enfant", user=user_id, parent=todo_c.uuid)
    repo_memory.save(todo_d)
    
    todo_e = Todo(title="Arrière-Arrière-Petit-Enfant", user=user_id,parent=todo_d.uuid)
    repo_memory.save(todo_e)

    # 2. Assertions sur la logique récursive brute
    # Parent (A) doit avoir 4 descendants (B, C, D, E)
    _, _, countchildrecursiv, _ = use_case.execute(todo_a.uuid, user_id)
    assert countchildrecursiv == 4
    # Enfant (B) doit avoir 3 descendants (C, D, E)
    _, _, countchildrecursiv, _ = use_case.execute(todo_b.uuid, user_id)
    assert countchildrecursiv == 3
    # Petit-Enfant (C) doit avoir 2 descendants (D, E)
    _, _, countchildrecursiv, _ = use_case.execute(todo_c.uuid, user_id)
    assert countchildrecursiv == 2
     # Arrière-Petit-Enfant (D) doit avoir 1 descendants (E)
    _, _, countchildrecursiv, _ = use_case.execute(todo_d.uuid, user_id)
    assert countchildrecursiv == 1   
    # Le dernier Arrière-Arrière-Petit-Enfant (E) doit avoir 0 descendants
    _, _, countchildrecursiv, _ = use_case.execute(todo_e.uuid, user_id)
    assert countchildrecursiv == 0