from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.cli.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_cli_recursive_parent_validation_cascade(repository, monkeypatch):
    # GIVEN
    user_id = uuid4()
    monkeypatch.setattr(
        "todo_bene.infrastructure.cli.main.load_user_config", lambda: user_id
    )

    # Création de la chaîne : G (racine) -> P -> E
    g = Todo(title="Grand-Parent", user=user_id)
    repository.save(g)
    p = Todo(title="Parent", user=user_id, parent=g.uuid)
    repository.save(p)
    e = Todo(title="Enfant", user=user_id, parent=p.uuid)
    repository.save(e)
    # Simulation des entrées :
    # 1. '1' -> Choisir le Grand-Parent dans la liste initiale
    # 2. '1' -> Choisir le Parent dans la vue détail du Grand-Parent
    # 3. '1' -> Choisir l'Enfant dans la vue détail du Parent
    # 4. 't' -> Terminer l'Enfant
    # 5. 'y' -> Valider le Parent ? (Oui)
    # 6. 'y' -> Valider le Grand-Parent ? (Oui)
    # 7. 'n' -> Répéter le Grand-Parent ? (Non)
    inputs = "1\n1\n1\nt\ny\ny\nn\n"

    # WHEN
    result = runner.invoke(app, ["list"], input=inputs)

    # THEN
    # Vérification des états en base de données
    assert repository.get_by_id(e.uuid).state is True, "L'enfant devrait être terminé"
    assert repository.get_by_id(p.uuid).state is True, (
        "Le parent devrait être terminé par cascade"
    )
    assert repository.get_by_id(g.uuid).state is True, (
        "Le grand-parent devrait être terminé par cascade"
    )

    # Vérification des messages dans la console
    assert "Valider aussi le parent 'Parent' ?" in result.stdout
    assert "Valider aussi le parent 'Grand-Parent' ?" in result.stdout
    assert (
        "' Grand-Parent ' est une tâche racine. Voulez-vous la répéter ?"
        in result.stdout
    )
