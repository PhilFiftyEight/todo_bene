from uuid import uuid4
import pytest
import os
from typer.testing import CliRunner
from typer.utils import _param_type_to_user_string
from todo_bene.infrastructure.cli.main import app  # Ou l'endroit où ton 'app' Typer est définie
from todo_bene.infrastructure.config import load_full_config, save_user_config,decrypt_value

runner = CliRunner()

try:
    # nécessaire avec le chiffrement de la base et la création systématique de la clé pendant les tests
    os.remove("test.db")
except FileNotFoundError:
    pass

def test_mail_setup_flow(tmp_path, monkeypatch):
    """Vérifie que la commande 'tb mail setup' enregistre bien les données."""
    # 1. Setup environnement de test
    config_file = tmp_path / "config.json"
    monkeypatch.setenv("TODO_BENE_CONFIG_PATH", str(config_file))

    # On crée un profil par défaut pour que la commande puisse s'y greffer
    save_user_config(uuid4(), "test.db", "default")

    # Simulation de la saisie utilisateur (Inputs séquentiels)
    # Host, Port, User, Password, Confirm Password
    inputs = "smtp.gmail.com\n587\ntest@gmail.com\nsecret123\nsecret123\n"

    result = runner.invoke(app, ["mail", "setup"], input=inputs)

    # Assertions
    assert result.exit_code == 0
    assert "Configuration SMTP sauvegardée" in result.stdout

    # Vérification du stockage réel
    config = load_full_config()
    smtp_cfg = config["profiles"]["default"]["smtp_config"]

    assert smtp_cfg["host"] == "smtp.gmail.com"
    assert decrypt_value(smtp_cfg["password_encrypted"]) == "secret123"
