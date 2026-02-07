import pendulum
from pendulum.parsing.exceptions import ParserError
from typing import List, Optional

from todo_bene.domain.entities.todo import Todo

class RepetitionTodo:
    def __init__(self, todo_repository):
        self.todo_repository = todo_repository

    def execute(self, todo_id: str) -> List[Todo] | None:
        original_todo = self.todo_repository.get_by_id(todo_id)
        
        # Garde-fous (Racine terminée uniquement) (Règle 1)
        if not original_todo or not original_todo.state or original_todo.parent:
            return None

        # La fréquence est obligatoire pour déclencher la répétition
        if not original_todo.frequency:
            raise ValueError(f"Cannot repeat todo {todo_id} without a frequency set.")
            
        # --- LOGIQUE DE DATES (Règle 3) ---
        tz = pendulum.local_timezone()
        # On récupère l'objet DateTime complet de l'original pour garder l'heure
        original_dt = pendulum.from_timestamp(original_todo.date_start, tz=tz)
        
        # a. Déterminer le nouveau jour de départ
        if original_todo.frequency == "tomorrow":
            new_start_dt = original_dt.add(days=1)
        else:
            try:
                # On parse la date fournie par la CLI
                parsed_date = pendulum.parse(original_todo.frequency, tz=tz)
                
                # STRICT : On injecte l'heure/min/sec exactes de l'original sur le nouveau jour
                new_start_dt = parsed_date.at(
                    original_dt.hour, 
                    original_dt.minute, 
                    original_dt.second
                )
            except (ParserError, ValueError, TypeError):
                # Plus de fallback : si on ne comprend pas la date, on stoppe tout
                raise ValueError(f"Instruction de répétition invalide, (format de date) : '{original_todo.frequency}'")
        
        # b. Calculer le delta en secondes par rapport à l'ancien start
        time_delta = new_start_dt.int_timestamp - original_todo.date_start

        created_todos: List[Todo] = []
        
        # Cloner la racine (la fréquence devient vide sur le clone)
        new_root = self._create_clone(original_todo, time_delta=time_delta)
        self.todo_repository.save(new_root)
        created_todos.append(new_root)
        
        # Cloner les descendants récursivement (Règle 2)
        self._clone_descendants(original_todo.uuid, new_root.uuid, created_todos, time_delta)
        
        return created_todos

    def _clone_descendants(self, old_parent_id, new_parent_id, created_list, time_delta):
        """Cherche et duplique récursivement tous les enfants avec le même delta."""
        children = self.todo_repository.find_by_parent(old_parent_id)
        for child in children:
            new_child = self._create_clone(child, new_parent_id=new_parent_id, time_delta=time_delta)
            self.todo_repository.save(new_child)
            created_list.append(new_child)
            # Appel récursif pour les niveaux inférieurs
            self._clone_descendants(child.uuid, new_child.uuid, created_list, time_delta)

    def _create_clone(self, source: Todo, new_parent_id: Optional[str] = None, time_delta: int = 0) -> Todo:
        """
        Crée une copie d'un Todo avec un décalage temporel.
        La fréquence est réinitialisée à vide pour éviter les répétitions en boucle.
        """
        return Todo(
            title=source.title,
            user=source.user,
            category=source.category,
            description=source.description,
            priority=source.priority,
            parent=new_parent_id,
            # On applique le décalage aux timestamps originaux
            date_start=source.date_start + time_delta,
            date_due=source.date_due + time_delta,
            frequency="" 
        )
