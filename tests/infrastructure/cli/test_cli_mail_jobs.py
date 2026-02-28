import pytest
from typer.testing import CliRunner
from todo_bene.infrastructure.cli.main import app
from todo_bene.infrastructure.config import load_full_config, decrypt_value, save_user_config
from uuid import uuid4

runner = CliRunner()

def test_add_mail_job_flow_with_questionary(tmp_path, monkeypatch, mocker):
    """Vérifie le flux CLI avec le mock de Questionary via pytest-mock."""
    # 1. Setup environnement
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))
    
    save_user_config(uuid4(), "test.db", "default")

    # 2. Mocking de Questionary (Focus Unique)
    # On mocke l'objet retourné par checkbox().ask()
    mock_ask = mocker.patch("questionary.checkbox")
    mock_ask.return_value.ask.return_value = ["format_phone", "waze_link"]
    
    # 3. Exécution de la commande
    # Seuls le nom et l'email sont passés via stdin (Typer prompts)
    inputs = "Rapport\nboss@test.com\n"
    result = runner.invoke(app, ["mail", "add-job"], input=inputs)

    # 4. Assertions
    assert result.exit_code == 0
    assert "Job 'Rapport' créé avec succès" in result.stdout
    
    # Vérification finale de la persistence
    config = load_full_config()
    job = config["profiles"]["default"]["mail_jobs"]["Rapport"]
    assert "format_phone" in job["transformers"]
