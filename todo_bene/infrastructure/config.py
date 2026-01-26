import json
import os
from pathlib import Path
from uuid import UUID
from typing import Any, Dict, Optional
import pendulum


def get_config_path() -> Path:
    """Retourne le chemin du fichier de configuration, configurable via variable d'environnement."""
    return Path(
        os.getenv("TODO_BENE_CONFIG_PATH", str(Path.home() / ".todo_bene.json"))
    )

def load_full_config() -> Dict[str, Any]:
    """Charge l'intégralité du dictionnaire de configuration."""
    path = get_config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}

def save_full_config(config: Dict[str, Any]):
    """Sauvegarde le dictionnaire complet dans le fichier JSON."""
    get_config_path().write_text(json.dumps(config, indent=4))

def load_user_config() -> UUID | None:
    data = load_full_config()
    try:
        return UUID(data["user_id"]) if "user_id" in data else None
    except (KeyError, ValueError):
        return None

def save_user_config(user_id: UUID):
    config = load_full_config()
    config["user_id"] = str(user_id)
    save_full_config(config)

# --- last_postpone_date is a flag To update todos that have passed their due date, once a day (first use)

def get_last_postpone_date() -> Optional[str]:
    """Récupère la date (YYYY-MM-DD) du dernier report automatique."""
    return load_full_config().get("last_auto_postpone")

def update_last_postpone_date():
    """Enregistre la date d'aujourd'hui comme date de dernier report."""
    config = load_full_config()
    config["last_auto_postpone"] = pendulum.now().to_date_string()
    save_full_config(config)