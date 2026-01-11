from dataclasses import dataclass, field
from uuid import UUID, uuid4
import pendulum

@dataclass
class Todo:
    title: str
    user: UUID  # On utilise le type UUID directement
    category: str = "Quotidien"  # Valeur par défaut
    description: str = "" # Valeur par défaut
    # Identifiant unique de cette tâche
    uuid: UUID = field(default_factory=uuid4)
    # Pointe vers l'UUID d'un Todo parent (pour les sous-tâches)
    parent: UUID | None = None
    state: bool = field(init=False, default=False)
    date_start: int | str = ""
    date_due: int | str = ""
    date_final: int = 0
    frequency: str | tuple[str, int] = ""
    priority: bool = False

    def __post_init__(self):
        # S'assure que user est bien un objet UUID si une string est passée
        if isinstance(self.user, str):
            self.user = UUID(self.user)

        # Gestion centralisée des dates pour éviter la répétition
        now = pendulum.now(pendulum.local_timezone()).int_timestamp
        self.date_start = self._parse_date(self.date_start) or now
        self.date_due = self._parse_date(self.date_due) or self.date_start

        # Parsing de la fréquence plus robuste
        if isinstance(self.frequency, str) and "," in self.frequency:
            parts = self.frequency.split(",")
            if len(parts) == 2:
                when, how = parts
                self.frequency = (when.strip(), int(how.strip()))

    def _parse_date(self, value: int | str) -> int | None:
        """Helper pour convertir les entrées en timestamp int."""
        if not value:
            return None
        if isinstance(value, int):
            return value
        return pendulum.from_format(
            value, "YYYY-MM-DD HH:mm:ss", pendulum.local_timezone(), "fr"
        ).int_timestamp