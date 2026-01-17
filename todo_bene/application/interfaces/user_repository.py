from abc import ABC, abstractmethod
from todo_bene.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        """Sauvegarde un utilisateur dans le système de persistance."""
        pass
