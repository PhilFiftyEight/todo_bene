from abc import ABC, abstractmethod
from uuid import UUID
from typing import List
from todo_bene.domain.entities.category import Category


class CategoryRepository(ABC):
    @abstractmethod
    def save_category(self, category: Category) -> None:
        """Enregistre une nouvelle catégorie personnalisée pour un utilisateur."""
        pass

    @abstractmethod
    def category_exists(self, name: str, user_id: UUID) -> bool:
        """
        Vérifie si une catégorie existe déjà pour cet utilisateur.
        La vérification doit être insensible à la casse et aux espaces.
        """
        pass

    @abstractmethod
    def get_all_categories(self, user_id: UUID) -> List[str]:
        """
        Récupère la liste des noms de toutes les catégories personnalisées
        créées par l'utilisateur.
        """
        pass
