from abc import ABC, abstractmethod
from uuid import UUID
from todo_bene.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def save_user(self, user: User) -> None:
        """Sauvegarde un utilisateur dans le système de persistance."""
        pass

    @abstractmethod
    def get_user_by_email(self, email: str):
        """Obtient le user par son email dans le système de persistance"""
        pass

    @abstractmethod
    def get_by_id(self, uuid: UUID):
        """On obtient le user par son uuid dans le système de persistance"""
        pass
