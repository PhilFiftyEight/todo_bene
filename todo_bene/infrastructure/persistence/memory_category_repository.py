from typing import List
from uuid import UUID

from todo_bene.domain.entities.category import Category
from todo_bene.application.interfaces.category_repository import CategoryRepository

class MemoryCategoryRepository(CategoryRepository):
    def __init__(self):
        self.categories = {} # Clé: (user_id, name_lower)

    def save_category(self, category: Category) -> None:
        """Enregistre une nouvelle catégorie personnalisée pour un utilisateur."""
        self.categories[(category.user_id, category.name)] = category

    def category_exists(self, name: str, user_id: UUID) -> bool:
        """
        Vérifie si une catégorie existe déjà pour cet utilisateur.
        La vérification doit être insensible à la casse et aux espaces.
        """
        return (user_id, name) in self.categories

    def get_all_categories(self, user_id: UUID) -> List[str]:
        """
        Récupère la liste des noms de toutes les catégories personnalisées 
        créées par l'utilisateur.
        """
        return [c.name for (uid, _), c in self.categories.items() if uid == user_id]