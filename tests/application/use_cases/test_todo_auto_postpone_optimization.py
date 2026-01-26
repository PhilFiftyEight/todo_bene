import pytest  # noqa: F401
import pendulum
from uuid import uuid4
from todo_bene.application.use_cases.todo_find_top_level_by_user import TodoGetAllRootsByUserUseCase, apply_auto_postpone
from todo_bene.domain.entities.todo import Todo

def test_auto_postpone_only_executes_once_per_day(repository, time_machine, mocker):
    # --- SETUP ---
    user_id = uuid4()
    
    # 1. On part de MAINTENANT (Lundi)
    # start_time = pendulum.datetime(2026, 1, 26, 10, 0, 0)
    start_time = pendulum.now(tz="Europe/Paris")
    time_machine.move_to(start_time)
    
    # Mock de la config (fichiers locaux)
    mock_update = mocker.patch("todo_bene.application.use_cases.todo_find_top_level_by_user.update_last_postpone_date")
    mock_get = mocker.patch("todo_bene.application.use_cases.todo_find_top_level_by_user.get_last_postpone_date", return_value=None)

    # 2. On crée un Todo VALIDE (échéance ce soir)
    due_today = start_time.at(23, 59, 59).timestamp()
    valid_todo = Todo(
        title="Tâche normale",
        user=user_id,
        date_start=start_time.timestamp(),
        date_due=due_today
    )
    repository.save(valid_todo)
    
    # Espions
    spy_find = mocker.spy(repository, "find_all_active_by_user")
    spy_save = mocker.spy(repository, "save")

    use_case = TodoGetAllRootsByUserUseCase(repository)

    # 3. ON VOYAGE DANS LE FUTUR (Mardi)
    # La tâche est maintenant en retard
    tomorrow = start_time.add(days=1)
    time_machine.move_to(tomorrow)

    # --- ACTION 1 : Premier appel du jour ---
    use_case.execute(user_id)

    # --- ASSERT 1 ---
    assert spy_find.call_count == 1
    # On vérifie que save a été appelé pour mettre à jour la date_due
    assert spy_save.call_count >= 1 
    mock_update.assert_called_once()

    # --- ACTION 2 : Deuxième appel le même jour ---
    mock_get.return_value = tomorrow.to_date_string()
    
    use_case.execute(user_id)

    # --- ASSERT 2 ---
    # Pas de nouvel appel à la base de données pour le scan
    assert spy_find.call_count == 1 
    # Pas de nouvel appel à l'écriture config
    assert mock_update.call_count == 1


def test_auto_postpone_returns_count_of_affected_todos(repository, time_machine, mocker):
    # --- SETUP ---
    user_id = uuid4()
    
    # 1. On part de MAINTENANT (Lundi)
    start_time = pendulum.datetime(2026, 1, 26, 10, 0, 0)
    time_machine.move_to(start_time)
    
    # Mocks des accès config (on cible le fichier du Use Case pour le patch)
    mocker.patch("todo_bene.application.use_cases.todo_find_top_level_by_user.get_last_postpone_date", return_value=None)
    mocker.patch("todo_bene.application.use_cases.todo_find_top_level_by_user.update_last_postpone_date")

    # 2. On crée un Todo qui sera en retard demain
    due_today = start_time.at(23, 59, 59).timestamp()
    repository.save(Todo(
        title="Tâche à reporter",
        user=user_id,
        date_start=start_time.timestamp(),
        date_due=due_today
    ))
    
    # 3. ON VOYAGE DANS LE FUTUR (Mardi)
    tomorrow = start_time.add(days=1)
    time_machine.move_to(tomorrow)

    # --- ACTION 1 : Premier appel ---
    # On teste directement la fonction apply_auto_postpone
    count = apply_auto_postpone(repository, user_id)

    # --- ASSERT 1 ---
    # On s'attend à ce que la fonction nous dise qu'elle a modifié 1 tâche
    assert count == 1

    # --- ACTION 2 : Deuxième appel (simulant l'optimisation) ---
    # On change le mock pour simuler que le fichier config contient la date du jour
    mocker.patch("todo_bene.application.use_cases.todo_find_top_level_by_user.get_last_postpone_date", return_value=tomorrow.to_date_string())
    
    count_opti = apply_auto_postpone(repository, user_id)

    # --- ASSERT 2 ---
    # L'optimisation doit renvoyer 0 (aucune tâche traitée car court-circuit)
    assert count_opti == 0