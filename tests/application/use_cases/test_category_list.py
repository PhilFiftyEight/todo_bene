from todo_bene.application.use_cases.category_list import CategoryListUseCase
from todo_bene.infrastructure.persistence.memory.memory_category_repository import (
    MemoryCategoryRepository,
)
from todo_bene.domain.entities.category import Category


def test_category_list_merges_system_and_custom(user_id):
    # Arrange
    repo = MemoryCategoryRepository()
    use_case = CategoryListUseCase(repo)

    # On ajoute une catégorie perso
    repo.save_category(Category(name="Jardinage", user_id=user_id))

    # Act
    categories = use_case.execute(user_id=user_id)

    # Assert
    # Doit contenir les 6 de base + "Jardinage"
    assert "Quotidien" in categories
    assert "Jardinage" in categories
    assert len(categories) == 7
    # Bonus : vérifier que c'est trié par ordre alphabétique
    assert categories == sorted(categories)

def test_category_list_uniqueness_with_emoji_logic(user_id):
    """Vérifie que même si on essaie d'ajouter une catégorie système, la liste reste propre."""
    repo = MemoryCategoryRepository()
    use_case = CategoryListUseCase(repo)

    # On force l'ajout d'une catégorie qui a le même nom qu'une catégorie système
    # (Même si le UseCase de création l'empêche, on teste la robustesse du List)
    repo.save_category(Category(name="Travail", user_id=user_id))

    categories = use_case.execute(user_id=user_id)

    # Assert
    assert categories.count("Travail") == 1
    assert len(categories) == 6 # Pas de 7ème catégorie "doublon"