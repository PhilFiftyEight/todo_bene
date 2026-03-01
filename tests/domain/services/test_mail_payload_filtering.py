import pytest
import pendulum
from uuid import uuid4
from todo_bene.domain.entities.todo import Todo
from todo_bene.domain.services.mail_engine import filter_todos_for_job


def test_filter_and_sort_mail_payload_with_hierarchy():
    user_id = uuid4()
    tz = pendulum.local_timezone()
    
    # Référence temporelle : Aujourd'hui (puisque tout est reporté au matin même)
    now = pendulum.now(tz)
    today_ts = now.at(12, 0, 0).int_timestamp
    future_ts = now.add(days=1).int_timestamp

    # --- SETUP DES DATA ---
    
    # 1. P1 : Parent Urgent (Aujourd'hui) + Prioritaire
    p1_id = uuid4()
    p1 = Todo(
        title="P1", user=user_id, uuid=p1_id, 
        date_due=today_ts, priority=True, category="Work"
    )
    # C1 : Enfant de P1 (Aujourd'hui) -> Doit apparaître
    c1 = Todo(
        title="C1", user=user_id, parent=p1_id, 
        date_due=today_ts, category="Work"
    )

    # 2. P2 : Parent Normal (Aujourd'hui)
    p2_id = uuid4()
    p2 = Todo(
        title="P2", user=user_id, uuid=p2_id, 
        date_due=today_ts, priority=False, category="Work"
    )
    # C2 : Enfant de P2 (Demain) -> Doit apparaître CAR porté par P2 qui est dû
    c2 = Todo(
        title="C2", user=user_id, parent=p2_id, 
        date_due=future_ts, category="Work"
    )

    # 3. KO : Catégorie exclue (Home)
    todo_excluded = Todo(
        title="Excluded", user=user_id, 
        date_due=today_ts, category="Home"
    )

    # 4. KO : Terminé
    todo_done = Todo(
        title="Done", user=user_id, 
        date_due=today_ts, state=True, category="Work"
    )

    all_todos = [p2, c2, p1, c1, todo_excluded, todo_done]

    # --- EXECUTION ---
    # On demande Work, on exclut Home
    result = filter_todos_for_job(
        todos=all_todos,
        include_cats=["Work"],
        exclude_cats=["Home"]
    )

    # --- ASSERTIONS ---
    
    # On s'attend à 4 todos (P1, C1, P2, C2)
    assert len(result) == 4
    
    # Vérification du Tri : P1 est Prioritaire + Aujourd'hui -> Index 0
    assert result[0].title == "P1"
    
    # Vérification de l'exclusion
    titles = [t.title for t in result]
    assert "Excluded" not in titles
    assert "Done" not in titles
    
    # Vérification du maintien de la hiérarchie (C2 est là malgré date future)
    assert "C2" in titles


def test_filter_and_sort_mail_payload_with_completed_child_context():
    user_id = uuid4()
    tz = pendulum.local_timezone()
    
    # Référence temporelle : Aujourd'hui
    now = pendulum.now(tz)
    today_ts = now.at(12, 0, 0).int_timestamp

    # --- SETUP DES DATA ---
    
    # 1. Parent (P1) : Actif et dû aujourd'hui
    p1_id = uuid4()
    p1 = Todo(
        title="Appeler Client", 
        user=user_id, 
        uuid=p1_id, 
        date_due=today_ts, 
        category="Work",
        state=False
    )
    
    # 2. Enfant (C1) : TERMINÉ (state=True) mais contient une info cruciale
    # Il doit figurer dans le mail car son parent P1 est actif.
    c1 = Todo(
        title="Trouver numéro : 0601020304", 
        user=user_id, 
        parent=p1_id, 
        date_due=today_ts, 
        category="Work",
        state=True  # <--- Terminé
    )

    # 3. Autre tâche (T2) : Terminée SANS parent actif (ou sans parent du tout)
    # Celle-ci ne doit PAS figurer dans le mail.
    t2 = Todo(
        title="Ancienne tâche finie", 
        user=user_id, 
        date_due=today_ts, 
        state=True, 
        category="Work"
    )

    all_todos = [p1, c1, t2]

    # --- EXECUTION ---
    result = filter_todos_for_job(
        todos=all_todos,
        include_cats=["Work"],
        exclude_cats=[]
    )

    # --- ASSERTIONS ---
    
    # On s'attend à avoir P1 et C1, mais pas T2.
    assert len(result) == 2
    
    titles = [t.title for t in result]
    assert "Appeler Client" in titles
    assert "Trouver numéro : 0601020304" in titles
    assert "Ancienne tâche finie" not in titles
    
    # Vérification que l'enfant est bien marqué comme terminé dans le résultat
    child_in_res = next(t for t in result if t.title == "Trouver numéro : 0601020304")
    assert child_in_res.state is True