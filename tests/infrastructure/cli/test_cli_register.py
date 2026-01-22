import json

# import getpass
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app

runner = CliRunner()


def test_cli_register_success(monkeypatch, test_config_env):
    """Vérifie le succès de l'enregistrement."""
    #monkeypatch.setattr("getpass.getuser", lambda: "philippe")

    # Act
    result = runner.invoke(app, ["register"], input="phil@exemple.com\n")

    # Assert
    assert result.exit_code == 0
    import getpass
    assert f"Bienvenue {getpass.getuser()}" in result.stdout
    assert test_config_env.exists()

    with open(test_config_env, "r") as f:
        data = json.load(f)
        assert "user_id" in data

def test_commands_blocked_when_unregistered(test_config_env):
    """Vérifie que le wizard se lance si pas de profil."""
    if test_config_env.exists():
        test_config_env.unlink()

    # On simule l'appel à 'list'
    result = runner.invoke(app, ["list"], input="philippe@local\nphilippe\n")

    assert result.exit_code == 0
    # On vérifie que le processus de création a eu lieu
    assert "Email inconnu" in result.stdout
    assert "Profil créé" in result.stdout
