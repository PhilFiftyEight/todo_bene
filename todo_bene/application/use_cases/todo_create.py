from uuid import UUID
from typing import Optional
import pendulum
from todo_bene.domain.entities.todo import Todo


class TodoCreateUseCase:
    def __init__(self, repository):
        self.repository = repository

    def _parse_flexible(self, date_str: str, tz) -> pendulum.DateTime:
        try:
            return pendulum.parse(date_str).replace(tzinfo=tz)
        except Exception:
            formats = [
                "DD/MM/YYYY HH:mm:ss",
                "DD/MM/YYYY HH:mm",
                "DD/MM/YYYY",
                "DD-MM-YYYY HH:mm:ss",
                "DD-MM-YYYY HH:mm",
                "DD-MM-YYYY",
            ]
            for fmt in formats:
                try:
                    return pendulum.from_format(date_str, fmt, tz=tz)
                except (ValueError, pendulum.parsing.exceptions.ParserError):
                    continue
            raise ValueError(f"Format de date non supporté : {date_str}")

    def execute(
        self,
        title: str,
        user: UUID,
        category: str = "Quotidien",
        description: str = "",
        priority: bool = False,
        date_start: str = "",
        date_due: str = "",
        parent: Optional[UUID] = None,
    ) -> Todo:
        tz = pendulum.local_timezone()

        # 1. Dates
        if date_start:
            dt_start = self._parse_flexible(date_start, tz)
            if len(date_start) <= 10:
                dt_start = dt_start.at(0, 0, 0)
        else:
            dt_start = pendulum.now(tz)

        if date_due:
            dt_due = self._parse_flexible(date_due, tz)
            if len(date_due) <= 10:
                dt_due = dt_due.at(23, 59, 59)
        else:
            dt_due = dt_start.at(23, 59, 59)

        # 2. Vérification Règle n°1 (Parentalité)
        if parent:
            parent_todo = self.repository.get_by_id(parent)
            if parent_todo:
                # On compare les timestamps (car l'entité stocke des int)
                if int(dt_due.timestamp()) > parent_todo.date_due:
                    raise ValueError(
                        "La date d'échéance de l'enfant ne peut pas dépasser celle du parent."
                    )

        # 3. Création de l'entité
        # ATTENTION : On passe les dates en string ISO pour que
        # le __post_init__ de Todo fasse le parsing vers timestamp.
        todo = Todo(
            title=title,
            user=user,  # Objet UUID
            category=category,
            description=description,
            priority=priority,
            date_start=dt_start.to_datetime_string(),
            date_due=dt_due.to_datetime_string(),
            parent=parent,  # Objet UUID ou None
        )
        self.repository.save(todo)
        return todo
