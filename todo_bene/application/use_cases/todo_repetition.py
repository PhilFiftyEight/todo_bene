from os import getenv
import pendulum
from pendulum.parsing.exceptions import ParserError
from typing import List, Optional

from todo_bene.domain.entities.todo import Todo
from todo_bene.domain.services.frequency_engine import FrequencyEngine
from todo_bene.domain.services.frequency_parser import FrequencyParser


class RepetitionTodo:
    def __init__(self, todo_repository):
        self.todo_repository = todo_repository
        self.frequency_parser = FrequencyParser(getenv("LANG")[:2])
        self.frequency_engine = FrequencyEngine()

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
        original_dt = pendulum.from_timestamp(original_todo.date_start, tz=tz)
        
        created_todos = []

        try:
            # Gestion du cas spécifique "tomorrow" (Règle métier par défaut)
            if original_todo.frequency == "tomorrow":
                occurrences = [original_dt.add(days=1)]
            else:
                # a. Récupération des dates via le parser et l'engine
                dsl_instruction = self.frequency_parser.parse(original_todo.frequency)
                occurrences = self.frequency_engine.get_occurrences(dsl_instruction)

            if not occurrences:
                raise ValueError("Aucune occurrence trouvée")

            # b. Boucle sur chaque occurrence pour créer une salve (Racine + Enfants)
            for next_date in occurrences:
                # On réinjecte l'heure/min/sec de l'original dans la date de l'engine
                # next_date peut être un DateTime (via engine) ou un objet pendulum (via tomorrow)
                target_dt = next_date.at(
                    original_dt.hour, 
                    original_dt.minute, 
                    original_dt.second
                ).in_timezone(tz)

                # Calcul du delta en secondes pour cette occurrence précise
                time_delta = target_dt.int_timestamp - original_todo.date_start

                # Création du clone de la racine
                new_root = self._create_clone(original_todo, time_delta=time_delta)
                self.todo_repository.save(new_root)
                created_todos.append(new_root)

                # Création des descendants pour cette occurrence (Règle 2)
                self._clone_descendants(original_todo.uuid, new_root.uuid, created_todos, time_delta)
                
        except Exception as e:
            # Si c'est déjà notre ValueError "Aucune occurrence", on la laisse remonter
            if str(e) == "Aucune occurrence trouvée":
                raise e
            # Sinon, on lève l'exception d'instruction invalide
            raise ValueError(f"Instruction de répétition invalide : '{original_todo.frequency}'")
        
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
