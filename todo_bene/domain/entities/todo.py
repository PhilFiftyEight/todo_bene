from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional, Union, Tuple
import pendulum


# Utils
def _parse_flexible_date(date_val: Union[str, int, float, None]) -> int:
    """Transforme une entrée date flexible en timestamp entier."""
    if not date_val:
        return 0
    if isinstance(date_val, (int, float)):
        return int(date_val)

    tz = pendulum.local_timezone()
    try:
        return pendulum.parse(date_val, strict=False, tz=tz).int_timestamp
    except pendulum.ParserError:
        return 0


@dataclass
class Todo:
    title: str
    user: UUID
    uuid: UUID = field(default_factory=uuid4)
    category: str = "Quotidien"
    description: str = ""
    parent: Optional[UUID] = None
    priority: bool = False
    frequency: Union[str, Tuple[str, int]] = ""
    state: bool = False
    date_start: Optional[int | str] = None
    date_due: Optional[int | str] = None
    date_final: int = 0

    def __post_init__(self):
        # 1. On délègue les conversions d'IDs et de fréquence
        self._init_identifiers()
        self._init_frequency()

        # 2. On centralise la logique métier des dates
        self._init_dates()

    def _init_identifiers(self):
        """Conversion des UUIDs."""
        if isinstance(self.user, str):
            self.user = UUID(self.user)
        if isinstance(self.uuid, str):
            self.uuid = UUID(self.uuid)
        if isinstance(self.parent, str) and self.parent:
            self.parent = UUID(self.parent)

    def _init_frequency(self):
        """Gestion de la fréquence."""
        if isinstance(self.frequency, str) and "," in self.frequency:
            parts = self.frequency.split(",")
            try:
                self.frequency = (parts[0], int(parts[1]))
            except (ValueError, IndexError):
                pass

    def _init_dates(self):
        """Logique métier des dates."""
        tz = pendulum.local_timezone()

        # Parsing initial
        ts_start = _parse_flexible_date(self.date_start)
        ts_due = _parse_flexible_date(self.date_due)
        self.date_final = _parse_flexible_date(self.date_final)

        # Règle : date_start par défaut
        if ts_start == 0:
            ts_start = pendulum.now(tz).int_timestamp

        # Règle : date_due par défaut (fin de journée du start)
        if ts_due == 0:
            dt_start = pendulum.from_timestamp(ts_start, tz=tz)
            ts_due = dt_start.at(23, 59, 59).int_timestamp

        # Règle : cohérence
        if ts_due < ts_start:
            ts_due = ts_start

        self.date_start = ts_start
        self.date_due = ts_due

    def update(self, **kwargs):
        """
        Met à jour les attributs autorisés avec validation de la 'génétique'.
        """
        # Liste blanche des champs modifiables (Sécurité)
        allowed_fields = {'title', 'description', 'category', 'priority', 'date_start', 'date_due'}
        
        # On extrait les valeurs pour la validation croisée
        # On prend la nouvelle valeur si fournie, sinon la valeur actuelle
        new_start = kwargs.get('date_start', self.date_start)
        new_due = kwargs.get('date_due', self.date_due)
        
        # Règle : Pas de date_start dans le passé (UNIQUEMENT si on tente de la modifier)
        if 'date_start' in kwargs:
            now_ts = pendulum.now().timestamp()
            # On garde une marge de 10s pour les tests/exécution
            if kwargs['date_start'] < (now_ts - 10):
                raise ValueError("La date de début ne peut pas être dans le passé")

        # Règle : Cohérence temporelle intrinsèque (Due >= Start)
        if new_due < new_start:
            raise ValueError("L'échéance doit être après le début")

        # Modification limitée aux champs autorisés
        forbiden_fields = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)
            else:
               forbiden_fields.append(key)
        return forbiden_fields
