from uuid import UUID
from todo_bene.application.interfaces.category_repository import CategoryRepository
from todo_bene.domain.entities.category import Category


class CategoryCreateUseCase:
    def __init__(self, repo: CategoryRepository):
        self.repo = repo

    def execute(self, name: str, user_id: UUID) -> Category:
        # Validation du domaine (vérifie si le nom est vide via __post_init__)
        # On passe le user_id à l'entité comme défini dans le fichier category.py
        category = Category(name=name, user_id=user_id)

        # Vérification des doublons avec les catégories système(=universelles) (insensible à la casse)
        is_system = any(category.name == system_cat for system_cat in Category.ALL)
        if is_system:
            raise ValueError("Cette catégorie existe déjà")

        # Vérification des doublons dans le repository (insensible à la casse)
        if self.repo.category_exists(category.name, user_id):
            raise ValueError("Cette catégorie existe déjà")

        # 5. Persistance
        self.repo.save_category(category)

        return category
