import duckdb
from uuid import UUID
from typing import List, Optional
from todo_bene.domain.entities.todo import Todo
from todo_bene.application.interfaces.todo_repository import TodoRepository


class DuckDBTodoRepository(TodoRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = duckdb.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                uuid UUID PRIMARY KEY,
                title VARCHAR,
                description TEXT,
                category VARCHAR,
                state BOOLEAN,
                priority BOOLEAN,
                date_start DOUBLE,
                date_due DOUBLE,
                user_id UUID,
                parent_id UUID
            )
        """)
        # AJOUT : La table users
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uuid UUID PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE
            )
        """)

    # AJOUT : Pour le support du bloc 'with'
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Fermeture explicite et sécurisée."""
        if self._conn:
            try:
                self._conn.close()
            except duckdb.Error:
                pass  # Ici, une erreur de fermeture est moins critique qu'un except nu

    def save(self, todo: Todo):
        self._conn.execute(
            """
            INSERT OR REPLACE INTO todos 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                todo.uuid,
                todo.title,
                todo.description,
                todo.category,
                todo.state,
                todo.priority,
                todo.date_start,
                todo.date_due,
                todo.user,
                todo.parent,
            ),
        )

    def get_by_id(self, todo_id: UUID) -> Optional[Todo]:
        res = self._conn.execute(
            "SELECT * FROM todos WHERE uuid = ?", (todo_id,)
        ).fetchone()
        if res:
            return self._row_to_todo(res)
        return None

    def find_top_level_by_user(self, user_id: UUID) -> List[Todo]:
        query = """
            SELECT * FROM todos 
            WHERE user_id = ? 
            AND parent_id IS NULL 
            AND state = false 
            ORDER BY date_start ASC
        """
        rows = self._conn.execute(query, (user_id,)).fetchall()
        return [self._row_to_todo(row) for row in rows]

    def find_by_parent(self, parent_id: UUID) -> List[Todo]:
        query = """
            SELECT * FROM todos 
            WHERE parent_id = ? 
            ORDER BY date_start ASC
        """
        rows = self._conn.execute(query, (parent_id,)).fetchall()
        return [self._row_to_todo(row) for row in rows]

    def search_by_title(self, user_id: UUID, search_term: str) -> List[Todo]:
        query = """
            SELECT * FROM todos 
            WHERE user_id = ? AND title ILIKE ?
            ORDER BY title ASC
            LIMIT 10
        """
        rows = self._conn.execute(query, (user_id, f"%{search_term}%")).fetchall()
        return [self._row_to_todo(row) for row in rows]

    def find_all_by_user(self, user_id: UUID) -> list[Todo]:
        """Récupère tous les todos de l'utilisateur, sans filtre hiérarchique."""
        with duckdb.connect(self.db_path) as conn:
            res = conn.execute(
                "SELECT * FROM todos WHERE user_id = ? ORDER BY date_start ASC",
                [str(user_id)],
            ).fetchall()
        # On utilise ta méthode de mapping existante
        return [self._row_to_todo(row) for row in res]

    def count_all_descendants(self, todo_uuid: UUID) -> int:
        """Compte récursivement tous les descendants d'un Todo."""
        children = self.find_by_parent(todo_uuid)
        total = len(children)
        for child in children:
            total += self.count_all_descendants(child.uuid)
        return total

    def delete(self, todo_id: UUID) -> None:
        """Supprime récursivement un todo et ses enfants via SQL."""
        query = """
            DELETE FROM todos WHERE uuid IN (
                WITH RECURSIVE tree AS (
                    SELECT uuid FROM todos WHERE uuid = ?
                    UNION ALL
                    SELECT t.uuid FROM todos t JOIN tree ON t.parent_id = tree.uuid
                )
                SELECT uuid FROM tree
            )
        """
        self._conn.execute(query, (todo_id,))

    def update_state(self, todo_id: UUID, state: bool) -> None:
        """Met à jour l'état d'un todo en base de données."""
        # Maintenant on peut mettre à jour
        self._conn.execute(
            "UPDATE todos SET state = ? WHERE uuid = ?", [state, str(todo_id)]
        )

    def get_pending_completion_parents(self, user_id: UUID) -> list[Todo]:
        # On cherche les tâches (P) non complétées
        # QUI ont des enfants
        # ET pour lesquelles il n'existe AUCUN enfant non complété
        query = """
                SELECT p.* FROM todos p
                WHERE p.user_id = ? 
                AND p.state = false
                AND EXISTS (SELECT 1 FROM todos c WHERE c.parent_id = p.uuid)
                AND NOT EXISTS (
                    SELECT 1 FROM todos c 
                    WHERE c.parent_id = p.uuid 
                    AND c.state = false
                )
            """
        # On utilise la connexion déjà ouverte de l'instance
        res = self._conn.execute(query, [str(user_id)]).fetchall()
        # On transforme les lignes en objets Todo (utilise ta méthode de mapping habituelle)
        return [self._row_to_todo(row) for row in res]

    def _row_to_todo(self, row) -> Todo:
        return Todo(
            uuid=row[0],
            title=row[1],
            description=row[2],
            category=row[3],
            state=row[4],
            priority=row[5],
            date_start=row[6],
            date_due=row[7],
            user=row[8],
            parent=row[9],
        )

    def get_user_by_email(self, email: str):
        """Recherche un utilisateur par son email."""
        result = self._conn.execute(
            "SELECT uuid, name, email FROM users WHERE email = ?",
            (email,)
        ).fetchone()
        
        if result:
            from todo_bene.domain.entities.user import User
            # result[0] est déjà un objet UUID grâce à DuckDB
            user_uuid = result[0] 
            
            # Sécurité : si jamais c'est une string, on la convertit, sinon on garde l'objet
            if isinstance(user_uuid, str):
                user_uuid = UUID(user_uuid)
                
            return User(uuid=user_uuid, name=result[1], email=result[2])
        return None
    
    def save_user(self, user):
        """Sauvegarde un utilisateur (Crée ou met à jour par UUID)."""
        self._conn.execute(
            """
            INSERT INTO users (uuid, name, email)
            VALUES (?, ?, ?)
            ON CONFLICT (uuid) DO UPDATE SET
                name = excluded.name,
                email = excluded.email
            """,
            (str(user.uuid), user.name, user.email),
        )
