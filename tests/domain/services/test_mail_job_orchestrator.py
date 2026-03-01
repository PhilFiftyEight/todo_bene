import pytest
import pendulum
import uuid
from todo_bene.domain.services.mail_engine import run_mail_jobs_background
from todo_bene.domain.entities.todo import Todo

@pytest.fixture
def base_setup(mocker):
    profile = "test_profile"
    user_id = uuid.uuid4()
    # ON PATCHE DANS LE MODULE DE DESTINATION (mail_engine)
    mocker.patch("todo_bene.domain.services.mail_engine.load_user_info", 
                 return_value=(user_id, "fake_db.sqlite", profile))

    mocker.patch("todo_bene.domain.services.mail_engine.load_full_config", 
                 return_value={}) # Sera écrasé dans le test, mais on initialise le patch ici
    
    mocker.patch("todo_bene.domain.services.mail_engine.decrypt_value", 
                 return_value="test@test.com")
    
    mocker.patch("todo_bene.domain.services.mail_engine.save_full_config")
    # Idem pour le calendrier s'il est importé directement
    mocker.patch("todo_bene.domain.services.calendar_service.is_send_day", 
                 return_value=True)
    return profile, user_id

def test_should_send_mail_if_not_sent_today(mocker, base_setup):
    profile_name, user_id = base_setup
    hier = pendulum.now().subtract(days=1).to_date_string()
    
    mock_config = {
        "profiles": {
            profile_name: {
                "mail_jobs": {
                    "home": {
                        "recipient": "HASH",
                        "last_mail_sent_date": hier,
                        "business_days_only": False,
                        "include_categories": ["Work"],
                        "exclude_categories": [],
                        "transformers": []
                    }
                }
            }
        }
    }
    
    # On cible explicitement l'usage dans mail_engine
    mocker.patch("todo_bene.domain.services.mail_engine.load_full_config", return_value=mock_config)
    mock_send = mocker.patch("todo_bene.domain.services.mail_engine.send_email_notification", return_value=True)
    
    # Création d'un Todo réel avec son user_id
    t = Todo(
        uuid=uuid.uuid4(),
        user=user_id,  
        title="Test Task",
        category="Work",
        state=False,
        date_due=0 # Échu (timestamp 1970)
    )
    
    run_mail_jobs_background([t])
    
    assert mock_send.called

def test_run_mail_jobs_filters_by_specific_job_config(mocker, base_setup):
    profile_name, user_id = base_setup
    mock_config = {
        "profiles": {
            profile_name: {
                "mail_jobs": {
                    "job_a": {
                        "recipient": "HASH_A",
                        "include_categories": ["Cat_A"],
                        "exclude_categories": [],
                        "transformers": []
                    },
                    "job_b": {
                        "recipient": "HASH_B",
                        "include_categories": ["Cat_B"],
                        "exclude_categories": [],
                        "transformers":  []
                    }
                }
            }
        }
    }
    # On patche les deux au bon endroit
    mocker.patch("todo_bene.domain.services.mail_engine.load_full_config", return_value=mock_config)
    mock_send = mocker.patch("todo_bene.domain.services.mail_engine.send_email_notification", return_value=True)

    # Deux todos pour deux catégories différentes
    t1 = Todo(uuid=uuid.uuid4(), user=user_id, title="Task A", category="Cat_A", state=False, date_due=0)
    t2 = Todo(uuid=uuid.uuid4(), user=user_id, title="Task B", category="Cat_B", state=False, date_due=0)

    run_mail_jobs_background([t1, t2])

    # Doit être appelé 2 fois car t1 va dans job_a et t2 dans job_b
    assert mock_send.call_count == 2