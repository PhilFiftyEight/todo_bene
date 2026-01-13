from uuid import UUID
import pendulum
import pytest  # noqa: F401
from todo_bene.domain.entities.todo import Todo
from todo_bene.domain.entities.user import User

@pytest.fixture
def get_User():
    return User('Jean', 'jean@dummy.org')

@pytest.fixture
def get_todo_dict(get_User: User):
    return {
        'title': 'Example',
        'user': get_User.uuid,
        'category': 'Quotidien',
        'description': "Simple exemple d'une tache à faire"
    }


# with required parameters only others not provided
def test_todo_creation_required_parameters(get_todo_dict: dict, get_User: User):
    user = get_User   
    todo = Todo(**get_todo_dict)

    # Assertions sur les types forts (UUID)
    assert todo.title == get_todo_dict['title']
    assert todo.user == user.uuid  # Comparaison directe d'objets UUID
    assert isinstance(todo.uuid, UUID) # La tâche a son propre ID
    assert todo.parent is None # Par défaut, pas de parent

    assert todo.category == get_todo_dict['category']
    assert todo.description == get_todo_dict['description']
    
    # Optionals not provided -> defaults values
    assert todo.date_final == 0                  # int <- timestamp (int), 0 car pas encore définie
    assert todo.frequency == ""                 # str, chaîne vide si non répétable
    assert not todo.state                       # Bool, Initial==False
    with pendulum.freeze():
        todo = Todo(**get_todo_dict)
        assert todo.date_start == pendulum.now(pendulum.local_timezone()).int_timestamp    # int <- timestamp (int)
        tz = pendulum.local_timezone()
        expected_due = pendulum.from_timestamp(todo.date_start, tz=tz).at(23, 59, 59).int_timestamp
        assert todo.date_due == expected_due # si due_date n'est pas définie alors elle est égale date_start à 23:59:00
        #assert todo.date_due == todo.date_start # si due_date n'est pas définie alors elle est égale date_start
    pendulum.travel_back()

# if at least one parameter required missing: TypeError
@pytest.mark.parametrize("missing_param", ["title", "user"])
def test_todo_creation_missing_required_parameters(get_todo_dict: dict, missing_param: str):
    """Vérifie que l'absence de n'importe quel argument obligatoire lève une TypeError spécifique."""
    # 1. On prépare les données en supprimant l'un des paramètres obligatoires
    todo_dict = get_todo_dict.copy()
    del todo_dict[missing_param]
    
    # 2. On vérifie que l'instanciation échoue
    with pytest.raises(TypeError) as excinfo:
        Todo(**todo_dict)
    
    # 3. On vérifie que le message d'erreur mentionne bien le paramètre manquant
    # Cela garantit que c'est bien la signature de la classe qui a levé l'erreur
    assert missing_param in str(excinfo.value)


# due_date is set : date_start different
def test_todo_creation_due_date_is_set(get_todo_dict: dict):
    todo = Todo(**get_todo_dict, date_start="2026-01-07 12:12:12", date_due="2026-01-17 12:12:12")
    assert todo.date_start != todo.date_due

#TODO parametrise pour tester plusieurs chaînes  
# frequency non vide car répétable, doit contenir un tuple précisant la façon et la répétition eg; tous les jours pendant 10 jours > ('j',10)
def test_todo_creation_frequency_is_not_empty(get_todo_dict: dict):
    todo = Todo(**get_todo_dict, frequency="j,10")
    assert todo.frequency == ('j', 10)

# attribut priority is a bool : False for 'normale', True for 'high'
def test_todo_creation_priority_bool(get_todo_dict: dict):
    # priority is not set : priority == False
    todo = Todo(**get_todo_dict)
    assert todo.priority is False
    # priority is set : priority == True
    todo = Todo(**get_todo_dict, priority=True)
    assert todo.priority is True


"""
# A tester dans les UseCases
- frequency non vide dans le Usecase de création l'analyse de ce champs doit créer les todos correspondants.
- parent contient bien l'uuid du parent dans le cas d'un sous-todo (à tester dans le UseCase Modification
- date_final fait partie du usecase Achèvement, à tester dans le test de celui-ci
"""