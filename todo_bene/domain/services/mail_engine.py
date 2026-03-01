import pendulum
import logging
from typing import List
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.config import (
    load_full_config, 
    save_full_config,  # Pour sauvegarder la config entière avec le nouveau verrou
    decrypt_value,
    load_user_info
)
from todo_bene.infrastructure.notifications import send_email_notification
from todo_bene.domain.services.calendar_service import is_send_day
from todo_bene.domain.services.transformer_service import apply_transformers

# Initialisation du logger
logger = logging.getLogger(__name__)

def filter_todos_for_job(
    todos: List[Todo], 
    include_cats: List[str], 
    exclude_cats: List[str]
) -> List[Todo]:
    """
    Filtre et trie les todos pour l'envoi du mail quotidien.
    """
    tz = pendulum.local_timezone()
    today_end = pendulum.now(tz).at(23, 59, 59).int_timestamp
    
    filtered = []
    
    # 1. Identification des IDs qui sont explicitement dûs et autorisés
    # (Sert de base pour inclure les enfants orphelins ou terminés plus tard)
    for todo in todos:
        # Check Catégorie
        is_allowed_cat = True
        if include_cats and todo.category not in include_cats:
            is_allowed_cat = False
        if exclude_cats and todo.category in exclude_cats:
            is_allowed_cat = False
            
        if not is_allowed_cat:
            continue

        # Règle de sélection de base : Non terminé ET (Échéance <= Aujourd'hui)
        is_due = todo.date_due <= today_end
        
        if not todo.state and is_due:
            filtered.append(todo)
        # Cas spécial du test : inclure C2 car son parent P2 est inclus
        elif todo.parent is not None:
            # On cherche si le parent est dans les sélectionnés
            parent_is_selected = any(t.uuid == todo.parent for t in todos if not t.state and t.date_due <= today_end)
            if parent_is_selected:
                filtered.append(todo)
    # 2. Tri : Priorité d'abord, puis Date d'échéance
    # (True > False, donc on trie priority en reverse)
    return sorted(
        filtered, 
        key=lambda x: (not x.priority, x.date_due, x.title)
    )


def prepare_todos_for_notification(todos, job_transformers):
    """
    Transforme les titres/descriptions et formate l'échéance.
    """
    prepared_list = []
    
    for t in todos:
        # 1. Application des transformers sur Titre et Description
        #
        clean_title = apply_transformers(t.title, job_transformers)
        clean_desc = apply_transformers(t.description or "", job_transformers)
        
        # 2. Formatage de l'heure (HH:MM)
        # On suppose que t.date_due est un timestamp ou un objet datetime
        # Formatage de l'heure avec Pendulum (HH:mm)
        due_time = "--:--"
        if t.date_due:
            due_time = pendulum.from_timestamp(t.date_due, tz=pendulum.local_timezone()).format("HH:mm")
        
        prepared_list.append({
            "title": clean_title,
            "description": clean_desc,
            "time": due_time
        })
        
    return prepared_list


def run_mail_jobs_background(all_todos: List[Todo]):
    """
    Orchestrateur (Thread) : Parcourt les jobs du profil actif et gère les envois.
    """
    user_id, db_path, profile_name = load_user_info()
    if not profile_name:
        return

    config = load_full_config() #
    profile = config.get("profiles", {}).get(profile_name, {})
    mail_jobs = profile.get("mail_jobs", {})
    
    if not mail_jobs:
        return

    today_str = pendulum.now().to_date_string()
    
    for job_name, job_params in mail_jobs.items():
        try:
            if job_params.get("last_mail_sent_date") == today_str:
                continue
            business_days_only = job_params.get("business_days_only", False)
            if not is_send_day(pendulum.now(), business_days_only):
                logger.info(f"Job '{job_name}' sauté : pas un jour d'envoi.")
                continue

            filtered = filter_todos_for_job(
                todos=all_todos,
                include_cats=job_params.get("include_categories", []),
                exclude_cats=job_params.get("exclude_categories", [])
            )

            if filtered:
                job_transformers = job_params.get("transformers")
                if job_transformers:
                    filtered = prepare_todos_for_notification(filtered, job_transformers)
                encrypted_recipient = job_params.get("recipient")
                recipient = decrypt_value(encrypted_recipient) #
                
                success = send_email_notification(
                    recipient=recipient,
                    todos=filtered,
                    subject=f"Tes tâches {job_name} du {today_str}"
                )

                if success:
                    # On met à jour la date dans le dictionnaire local
                    config["profiles"][profile_name]["mail_jobs"][job_name]["last_mail_sent_date"] = today_str
                    # On sauvegarde le dictionnaire complet
                    save_full_config(config)
                    logger.info(f"Job '{job_name}' envoyé avec succès.")
                    
        except Exception as e:
            logger.error(f"Erreur lors du traitement du job '{job_name}': {e}")