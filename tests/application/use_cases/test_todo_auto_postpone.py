import pytest  # noqa: F401
import pendulum
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.use_cases.todo_find_top_level_by_user import TodoGetAllRootsByUserUseCase


def test_postpone_triggered_by_get_all_roots(repository, user_id, time_machine):
    # 1. Setup à T=0
    start_time = pendulum.datetime(2026, 1, 1, 10, 0)
    time_machine.move_to(start_time)
    
    due_ts = start_time.at(23, 59, 59).timestamp()
    # On crée une tâche qui expire aujourd'hui à 23:59:59
    todo = Todo(title="Late Task", user=user_id, date_start=start_time.timestamp(), date_due=due_ts)
    repository.save(todo)

    # 2. Voyage dans le futur : T+1 jour (le lendemain)
    # La tâche est maintenant en retard
    time_machine.move_to(start_time.add(days=1))

    # Appel du Use Case existant 
    use_case = TodoGetAllRootsByUserUseCase(repository)
    use_case.execute(user_id)

    # 4. Vérification : La date_due doit avoir sauté à "aujourd'hui" (le jour du futur)
    updated = repository.get_by_id(todo.uuid)
    expected_due = pendulum.now().at(23, 59, 59).timestamp()
    
    assert updated.date_due == expected_due
