
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.config import save_user_config
from todo_bene.domain.entities.user import User
runner = CliRunner()

def test_add_todo_with_new_category_prompts_for_creation(repository, user_id):
    # GIVEN: Un utilisateur enregistré dans la config ET en base
    save_user_config(user_id)
    repository.save_user(User(uuid=user_id, name="Test User", email="test@example.com"))
    
    # WHEN: On tente d'ajouter un todo avec une catégorie inexistante "Voyage"
    # Note: On passe "Voyage" dans l'input SI ton prompt Typer attend une saisie, 
    # mais si tu utilises --category "Voyage", c'est un argument.
    # Ici, je simule l'argument et juste la réponse 'y' pour la confirmation.
    result = runner.invoke(app, ["add", "Prendre billets", "--category", "Voyage"], input="y\n")
    # THEN: La CLI doit confirmer la création
    assert result.exit_code == 0
    assert "La catégorie Voyage n'existe pas" in result.stdout
    assert "Catégorie Voyage créée" in result.stdout
    assert "Todo créé" in result.stdout
    # AND: On vérifie en base
    todos = repository.search_by_title(user_id, "Prendre billets")
    assert len(todos) > 0
    assert todos[0].category == "Voyage"
