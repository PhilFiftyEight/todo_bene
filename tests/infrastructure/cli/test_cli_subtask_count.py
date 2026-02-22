from typer.testing import CliRunner
from rich.text import Text
from todo_bene.infrastructure.cli.main import app, _display_detail_view
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_get import TodoGetUseCase
from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository


def test_cli_show_details_displays_recursive_count(user_id):
    repo_memory = MemoryTodoRepository()
    runner = CliRunner()
    
    # 1. Setup de la chaîne : Parent > Enfant > Petit-Enfant
    # Parent (A)
    todo_a = Todo(title="Parent", user=user_id)
    repo_memory.save(todo_a)
    
    # Enfant (B) -> aura 2 descendants (C et D)
    todo_b = Todo(title="Enfant", user=user_id, parent=todo_a.uuid)
    repo_memory.save(todo_b)
    
    # Petit-Enfant (C) -> aura 1 descendant (D)
    todo_c = Todo(title="Petit-Enfant", user=user_id, parent=todo_b.uuid)
    repo_memory.save(todo_c)
    
    # Arrière-Petit-Enfant (D)
    todo_d = Todo(title="Arriere-Petit-Enfant", user=user_id, parent=todo_c.uuid)
    repo_memory.save(todo_d)

    # 2. Exécution : On affiche les détails du Parent (A)
    # L'index dans la liste sera 1 pour le premier lancement
    #result = runner.invoke(app, ["list", "--period", "all"]) # Pour initialiser la vue
    # On simule la saisie de l'index du Parent pour voir ses détails
    # (Ou on appelle directement une commande de détail si elle existe, 
    # mais ici on teste l'affichage des sous-tâches de A)
    
    # Si on regarde les détails de 'Parent', on doit voir 'Enfant [+2]'
    # Si on regarde les détails de 'Enfant', on doit voir 'Petit-Enfant [+1]'
    
    
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        # On appelle directement la fonction de vue avec les datas du Use Case
        todo, children, count = TodoGetUseCase(repo_memory).execute(todo_a.uuid, user_id)
        _display_detail_view(todo, children, count, repo_memory)
    
    output = f.getvalue()
    plain_text = Text.from_ansi(output).plain
    # print(output)
    assert "Enfant [+2]" in plain_text

    # On descend dans l'Enfant (B)
    f_child = io.StringIO()
    with redirect_stdout(f_child):
        # On récupère les billes pour l'Enfant (B)
        todo_b_data, subtasks_b, count_b = TodoGetUseCase(repo_memory).execute(todo_b.uuid, user_id)
        _display_detail_view(todo_b_data, subtasks_b, count_b, repo_memory)
        
        output_b = Text.from_ansi(f_child.getvalue()).plain
        assert "Petit-Enfant [+1]" in output_b # C a un enfant (D)

    #  On descend dans le Petit-Enfant (C)
    f_grandchild = io.StringIO()
    with redirect_stdout(f_grandchild):
        # On récupère les billes pour le Petit-Enfant (C)
        todo_c_data, subtasks_c, count_c = TodoGetUseCase(repo_memory).execute(todo_c.uuid, user_id)
        _display_detail_view(todo_c_data, subtasks_c, count_c, repo_memory)

        output_c = Text.from_ansi(f_grandchild.getvalue()).plain
        assert "Arriere-Petit-Enfant" in output_c # D n'a plus d'enfants
        assert "[+0]" not in output_c
