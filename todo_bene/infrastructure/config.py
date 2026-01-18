import json
import os
from pathlib import Path
from uuid import UUID

def get_config_path() -> Path:
    """Retourne le chemin du fichier de configuration, configurable via variable d'environnement."""
    return Path(
        os.getenv("TODO_BENE_CONFIG_PATH", str(Path.home() / ".todo_bene.json"))
    )

def save_user_config(user_id: UUID):
    """Sauvegarde l'UUID de l'utilisateur dans le fichier JSON."""
    config = {"user_id": str(user_id)}
    # Utilisation de Path.write_text pour plus de simplicité et de sécurité
    get_config_path().write_text(json.dumps(config, indent=4))

def load_user_config() -> UUID | None:
    """Charge l'UUID de l'utilisateur. Retourne None si le fichier n'existe pas ou est invalide."""
    path = get_config_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return UUID(data["user_id"])
    except (json.JSONDecodeError, KeyError, ValueError, OSError):
        # On attrape les erreurs spécifiques plutôt qu'un except global
        return None