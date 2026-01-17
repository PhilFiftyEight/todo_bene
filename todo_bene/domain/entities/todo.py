from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional, Union, Tuple
import pendulum


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
        # 1. Gestion des IDs
        if isinstance(self.user, str):
            self.user = UUID(self.user)
        if isinstance(self.uuid, str):
            self.uuid = UUID(self.uuid)
        if isinstance(self.parent, str) and self.parent:
            self.parent = UUID(self.parent)

        # 2. Gestion de la Frequency (Conversion string "j,10" -> tuple ('j', 10))
        if isinstance(self.frequency, str) and "," in self.frequency:
            parts = self.frequency.split(",")
            try:
                self.frequency = (parts[0], int(parts[1]))
            except (ValueError, IndexError):
                pass

        tz = pendulum.local_timezone()
        now = pendulum.now(tz)

        if self.date_start is None:
            self.date_start = now.int_timestamp

        if self.date_due is None:
            # CORRECTION : On prend la fin de journée du start_date
            dt_start = pendulum.from_timestamp(self.date_start, tz=tz)
            self.date_due = dt_start.at(23, 59, 59).int_timestamp

        # 4. Conversion si les dates sont arrivées sous forme de chaînes
        if isinstance(self.date_start, str):
            self.date_start = self._parse_to_timestamp(self.date_start)

        if isinstance(self.date_due, str):
            self.date_due = self._parse_to_timestamp(self.date_due)

        if isinstance(self.date_final, str):
            self.date_final = self._parse_to_timestamp(self.date_final)
        elif self.date_final is None:
            self.date_final = 0

    def _parse_to_timestamp(self, date_str: str) -> int:
        if not date_str:
            return 0
        tz = pendulum.local_timezone()
        try:
            dt = pendulum.parse(date_str).replace(tzinfo=tz)
        except Exception:
            formats = [
                "DD/MM/YYYY HH:mm:ss",
                "DD/MM/YYYY HH:mm",
                "DD/MM/YYYY",
                "DD-MM-YYYY HH:mm:ss",
                "DD-MM-YYYY HH:mm",
                "DD-MM-YYYY",
            ]
            dt = None
            for fmt in formats:
                try:
                    dt = pendulum.from_format(date_str, fmt, tz=tz)
                    break
                except Exception:
                    continue
            if dt is None:
                raise ValueError(f"Format de date non reconnu : {date_str}")
        return dt.int_timestamp
