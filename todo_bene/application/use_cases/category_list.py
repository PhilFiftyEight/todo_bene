from uuid import UUID
from typing import List
from todo_bene.application.interfaces.category_repository import CategoryRepository
from todo_bene.domain.entities.category import Category


class CategoryListUseCase:
    def __init__(self, repo: CategoryRepository):
        self.repo = repo

    def execute(self, user_id: UUID) -> List[str]:
        # Récupérer les catégories système (définies dans le Domaine)
        system_categories = Category.ALL

        # Récupérer les catégories personnalisées de l'utilisateur via le Repo
        custom_categories = self.repo.get_all_categories(user_id)

        # Fusionner les deux listes
        # On utilise un set pour garantir l'unicité, même si le UseCase de création 
        # est déjà censé empêcher les doublons.
        # Retourner la liste triée alphabétiquement
        return sorted(list(set(system_categories + custom_categories)))
