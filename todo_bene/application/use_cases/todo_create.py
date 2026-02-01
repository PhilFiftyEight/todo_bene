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
        now = pendulum.now(tz)

        # Récupération du parent pour les règles de gestion
        parent_todo = None
        if parent:
            parent_todo = self.repository.get_by_id(parent)
            if not parent_todo:
                raise ValueError("Parent introuvable.")
            # Forçage silencieux : l'enfant hérite toujours de la catégorie du parent
            category = parent_todo.category   

        # Gestion de la date de début
        if date_start:
            dt_start = self._parse_flexible(date_start, tz)
            if len(date_start) <= 10:
                dt_start = dt_start.at(0, 0, 0)
            
            # Validation Racine dans le passé ---
            if not parent:
                if dt_start.start_of('day') < now.start_of('day'):
                    raise ValueError("Une tâche racine ne peut pas commencer dans le passé.")
            
            # Vérification date_start: Enfant >= Parent
            if parent_todo and int(dt_start.timestamp()) < parent_todo.date_start:
                raise ValueError(
                    "La date de début de l'enfant ne peut pas être antérieure à celle du parent."
                )
        elif parent_todo:
            # Règle Héritage de la date du parent si non fournie
            dt_start = pendulum.from_timestamp(parent_todo.date_start, tz=tz)
        else:
            # Cas racine par défaut
            dt_start = now

        # 3. Gestion de la date d'échéance
        if date_due:
            dt_due = self._parse_flexible(date_due, tz)
            if len(date_due) <= 10:
                dt_due = dt_due.at(23, 59, 59)
        else:
            # Par défaut, l'échéance est la fin de journée de la date de début
            dt_due = dt_start.at(23, 59, 59)

        # 4. Vérification Règle existante (Échéance Enfant <= Échéance Parent)
        if parent_todo:
            if int(dt_due.timestamp()) > parent_todo.date_due:
                raise ValueError(
                    "La date d'échéance de l'enfant ne peut pas dépasser celle du parent."
                )

        # 5. Création de l'entité
        todo = Todo(
            title=title,
            user=user,
            category=category,
            description=description,
            priority=priority,
            date_start=dt_start.to_datetime_string(),
            date_due=dt_due.to_datetime_string(),
            parent=parent,
        )
        
        self.repository.save(todo)
        return todo