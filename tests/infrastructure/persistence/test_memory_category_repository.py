import pytest
from uuid import uuid4
from todo_bene.application.use_cases.category_create import CategoryCreateUseCase
from todo_bene.infrastructure.persistence.memory.memory_category_repository import MemoryCategoryRepository

def test_memory_repo_integration_with_create_use_case():
    # Arrange
    repo = MemoryCategoryRepository()
    use_case = CategoryCreateUseCase(repo)
    user_id = uuid4()
    
    # Act
    # On crée une catégorie personnalisée via le Use Case
    # Le Use Case instancie Category, qui formate le nom en "Projet alpha" 
    # et lui donne l'émoji par défaut "🔖"
    cat_obj = use_case.execute("  projet alpha  ", user_id)
    
    # On récupère via la nouvelle méthode du repository
    categories = repo.get_all_categories_with_emojis(user_id)
    
    # Assert
    assert len(categories) == 1
    stored_cat = categories[0]
    
    assert stored_cat.name == "Projet alpha"  # Vérifie le formatage du domaine
    assert stored_cat.emoji == "🔖"            # Vérifie l'émoji par défaut
    assert stored_cat.user_id == user_id

def test_memory_repo_list_compatibility():
    # Vérifie que l'ancienne méthode get_all_categories fonctionne toujours
    repo = MemoryCategoryRepository()
    use_case = CategoryCreateUseCase(repo)
    user_id = uuid4()
    
    use_case.execute("Sport-Perso", user_id)
    
    names = repo.get_all_categories(user_id)
    assert names == ["Sport-perso"]