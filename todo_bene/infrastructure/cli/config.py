import json
import os
from pathlib import Path
from uuid import UUID

def get_config_path() -> Path:
    return Path(os.getenv("TODO_BENE_CONFIG_PATH", str(Path.home() / ".todo_bene.json")))

@property
def CONFIG_FILE():
    return get_config_path()

def save_user_config(user_id: UUID):
    config = {"user_id": str(user_id)}
    with open(get_config_path(), "w") as f:
        json.dump(config, f)

def load_user_config() -> UUID | None:
    path = get_config_path()
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
            return UUID(data["user_id"])
    except:  # noqa: E722
        return None