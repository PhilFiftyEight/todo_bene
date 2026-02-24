from typer.testing import CliRunner
from todo_bene.main import app
from todo_bene.domain.entities.todo import Todo
#from todo_bene.infrastructure.persistence.memory.memory_todo_repository import MemoryTodoRepository
from rich.text import Text

def test_cli_list_displays_inline_progress_bar(user_id, repository, monkeypatch,test_config_env):
    runner = CliRunner()
    #repo = MemoryTodoRepository()
    repo =repository
    
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_info",
        lambda: (user_id, "dev.db", "test_profile"),
    )


    # 1. Setup : Parent + 5 enfants (3 terminés)
    parent = Todo(title="Projet Alpha", user=user_id)
    repo.save(parent)
    
    for i in range(5):
        # 3 terminés (index 0, 1, 2), 2 en cours (3, 4)
        is_completed = i < 3
        child = Todo(
            title=f"Sub {i}", 
            user=user_id, 
            parent=parent.uuid, 
            state=is_completed
        )
        repo.save(child)

    # 2. Exécution
    result = runner.invoke(app, ["list", "--period", "all"],env={"TODO_BENE_CONFIG_PATH": str(test_config_env)})
    print("\n")
    
    # Nettoyage ANSI pour l'assertion
    plain_output = Text.from_ansi(result.stdout).plain
    # print(plain_output)
    # 3. Assertions
    # On vérifie la présence du titre et de l'amorce de la barre [5
    assert "Projet Alpha" in plain_output
    assert "[5" in plain_output
    # On vérifie qu'on voit bien les caractères de la barre (au moins un)
    assert "━" in result.stdout or "╸" in result.stdout