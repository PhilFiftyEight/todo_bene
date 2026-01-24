import pytest
from uuid import uuid4
from todo_bene.application.use_cases.category_create import CategoryCreateUseCase
from todo_bene.infrastructure.persistence.memory_category_repository import (
    MemoryCategoryRepository,
)
from todo_bene.domain.entities.category import Category

def test_category_create_success():
    # GIVEN
    category_repo = MemoryCategoryRepository()
    use_case = CategoryCreateUseCase(category_repo)
    user_id = uuid4()
    cat_name = "Jardinage"
    
    # WHEN
    category = use_case.execute(name=cat_name, user_id=user_id)
    
    # THEN
    assert category.name == "Jardinage"
    # On vérifie que le repository a bien reçu l'ordre d'enregistrement
    assert category_repo.category_exists(cat_name, user_id) is True

@pytest.mark.parametrize("existing_name, new_input", [
    ("Sport", "Sport"),   # Exactement le même
    ("Sport", "SPORT"),   # Casse différente
    ("Sport", " sport "), # Espaces et casse
    ("Sport", "sport"),   # Minuscules
    ('ESSAI', 'essai '),
])
def test_category_create_already_exists_raises_error(repository, existing_name, new_input):
    """Vérifie que la création échoue si la catégorie existe déjà (insensible à la casse/espaces)."""
    # GIVEN
    category_repo = MemoryCategoryRepository()
    use_case = CategoryCreateUseCase(category_repo)
    user_id = uuid4()
    
    # On simule que la catégorie existe déjà en base pour cet utilisateur
    # Note : Le repository de test doit supporter save_category
    category_repo.save_category(Category(name=existing_name, user_id=user_id))
    
    # WHEN / THEN
    with pytest.raises(ValueError, match="Cette catégorie existe déjà"):
        use_case.execute(name=new_input, user_id=user_id)
