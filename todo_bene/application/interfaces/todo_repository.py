from abc import ABC, abstractmethod
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

    # @abstractmethod
    # def find_by_user(self, user_id: UUID) -> list[Todo]:
    #     """Récupère tous les Todos appartenant à un utilisateur spécifique."""
    #     pass

    @abstractmethod
    def find_top_level_by_user(self, user_id: UUID) -> list[Todo]:
        """Récupère les Todos racines (sans parent) d'un utilisateur."""
        pass
