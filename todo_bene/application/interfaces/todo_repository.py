from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from todo_bene.domain.entities.todo import Todo


class TodoRepository(ABC):
    @abstractmethod
    def save(self, todo: Todo) -> None:
        pass

    @abstractmethod
    def get_by_id(self, todo_id: UUID) -> Todo | None:
        pass

    @abstractmethod
    def find_by_parent(self, parent_id: UUID) -> list[Todo]:
        pass

    @abstractmethod
    def find_all_active_by_user(self, user_id: UUID) -> list[Todo]:
        """Récupère toutes les tâches non terminées (actives) d'un utilisateur."""
        pass

    @abstractmethod
    def find_top_level_by_user(
        self, user_id: UUID, category: Optional[str] = None
    ) -> list[Todo]:
        """Récupère les tâches racines, avec un filtre optionnel par catégorie."""
        pass

    @abstractmethod
    def search_by_title(self, user_id: UUID, search_term: str) -> list[Todo]:
        pass

    @abstractmethod
    def delete(self, todo_id: UUID) -> None:
        """Supprime un Todo et toute sa descendance récursivement."""
        pass

    @abstractmethod
    def update_state(self, todo_id: UUID, state: bool) -> None:
        """Met à jour l'état (complété ou non) d'un Todo."""
        pass

    @abstractmethod
    def get_pending_completion_parents(self, user_id: UUID) -> list[Todo]:
        """
        Récupère les parents non complétés dont TOUS les enfants
        sont complétés (et qui ont au moins un enfant).
        """
        pass

    @abstractmethod
    def _row_to_todo(self, row: list) -> Todo:
        """Returns a Todo item from a list of data"""
        pass
