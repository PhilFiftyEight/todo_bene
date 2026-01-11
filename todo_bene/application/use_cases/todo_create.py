from uuid import UUID
from typing import Optional
import pendulum
from todo_bene.domain.entities.todo import Todo

class TodoCreateUseCase:
    def __init__(self, repository):
        self.repository = repository

    def _parse_flexible(self, date_str: str, tz) -> pendulum.DateTime:
        """Tente de parser en ISO, sinon en formats FR (slashs ou tirets)."""
        try:
            # Tente le standard ISO (YYYY-MM-DD)
            return pendulum.parse(date_str).replace(tzinfo=tz)
        except Exception:
            # Liste exhaustive des formats saisissables par un humain
            formats = [
                "DD/MM/YYYY HH:mm:ss", "DD/MM/YYYY HH:mm", "DD/MM/YYYY",
                "DD-MM-YYYY HH:mm:ss", "DD-MM-YYYY HH:mm", "DD-MM-YYYY"
            ]
            for fmt in formats:
                try:
                    return pendulum.from_format(date_str, fmt, tz=tz)
                except Exception:
                    continue
            raise ValueError(f"Format de date non supporté : {date_str}. Utilisez JJ/MM/AAAA ou AAAA-MM-JJ.")

    def execute(
        self, 
        title: str, 
        user: UUID, 
        category: str = "Quotidien", 
        description: str = "", 
        priority: bool = False,
        date_start: str = "",
        date_due: str = "",
        parent: Optional[UUID] = None
    ) -> Todo:
        tz = pendulum.local_timezone()
        
        # 1. Gestion Start
        if date_start:
            dt_start = self._parse_flexible(date_start, tz)
            # Si on a passé juste une date (longueur 10), on force 00:00:00
            if len(date_start) <= 10:
                dt_start = dt_start.at(0, 0, 0)
        else:
            dt_start = pendulum.now(tz)

        # 2. Gestion Due
        if date_due:
            dt_due = self._parse_flexible(date_due, tz)
            if len(date_due) <= 10:
                dt_due = dt_due.at(23, 59, 59)
        else:
            dt_due = dt_start.at(23, 59, 59)

        todo = Todo(
            title=title,
            user=user,
            category=category,
            description=description,
            priority=priority,
            date_start=dt_start.to_datetime_string(), # On repasse en ISO pour l'Entité
            date_due=dt_due.to_datetime_string(),
            parent=parent
        )
        self.repository.save(todo)
        return todo