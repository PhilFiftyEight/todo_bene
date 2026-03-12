import pendulum
from contextlib import contextmanager
from todo_bene.infrastructure.config import load_user_info
from todo_bene.infrastructure.persistence.duckdb.duckdb_connection_manager import DuckDBConnectionManager
from todo_bene.infrastructure.persistence.duckdb.duckdb_todo_repository import DuckDBTodoRepository
from todo_bene.infrastructure.persistence.duckdb.duckdb_category_repository import DuckDBCategoryRepository
from todo_bene.application.use_cases.todo_create import TodoCreateUseCase
from todo_bene.application.use_cases.category_create import CategoryCreateUseCase

@contextmanager
def get_repos():
    user_id, db_path, _ = load_user_info()
    with DuckDBConnectionManager(db_path) as conn:
    #conn = manager.get_connection()
        todo_repo = DuckDBTodoRepository(conn)
        cat_repo = DuckDBCategoryRepository(conn)
        yield user_id, todo_repo, cat_repo


def populate():
    with get_repos() as (user_id, todo_repo, cat_repo):
        now = pendulum.now(tz=pendulum.local_timezone())
        add_use_case = TodoCreateUseCase(todo_repo)
        
        # 1. Catégories personnalisées
        CategoryCreateUseCase(cat_repo).execute("Projet", user_id) #, "💰") pas prévu dans le use case
        # CategoryCreateUseCase(cat_repo).execute("Santé", user_id, "🏥")  # existe déja

        # 2. Scénario de tâches
        tasks = [
            ("Réparer fuite évier", "Quotidien", 0, True),
            ("Appeler Client A", "Travail", 0, True),
            ("Séance Squash", "Sport", 1, False),
            ("Review PR v0.4", "Travail", 3, True),
            ("Paiement TVA", "Finances", 10, False),
            ("Check-up Dentiste", "Santé", 45, False),
            ("Vacances Été", "Loisirs", 18, False),
            ("Créer Entreprise", "Projet", 20, False),
        ]

        for title, cat, days, prio in tasks:
            due = now.add(days=days).set(hour=18, minute=0)
            add_use_case.execute(
                title=title,
                description="Généré pour la démo v0.3.2",
                category=cat, user=user_id,
                date_start=now.format("DD-MM-YYYY HH:mm:ss"),
                date_due=due.format("DD-MM-YYYY HH:mm:ss"), priority=prio
            )

        # 3. Tâche complexe avec sous-tâches
        parent_id = add_use_case.execute(
            title="Projet Démo VHS", 
            description="Focus sur la vue détail", 
            category="Travail",
            user=user_id, 
            date_start=now.format("DD-MM-YYYY HH:mm:ss"), 
            date_due=now.add(days=1).format("DD-MM-YYYY HH:mm:ss"), 
            priority=True
        )
        add_use_case.execute(
            title="Installer VHS", 
            description="", 
            category="Travail", 
            user=user_id, 
            date_start=now.format("DD-MM-YYYY HH:mm:ss"), 
            date_due=now.format("DD-MM-YYYY HH:mm:ss"), 
            parent=parent_id.uuid
        )
        add_use_case.execute(
            title="Rédiger le .tape", 
            description="", 
            category="Travail", 
            user=user_id, 
            date_start=now.format("DD-MM-YYYY HH:mm:ss"), 
            date_due=now.format("DD-MM-YYYY HH:mm:ss"), 
            parent=parent_id.uuid, 
            priority=True
        )

    print(f"✅ Démo prête pour {user_id} !")

if __name__ == "__main__":
    populate()
