from todo_bene.application.use_cases.category_list import CategoryListUseCase
from todo_bene.infrastructure.persistence.memory_category_repository import MemoryCategoryRepository
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
    