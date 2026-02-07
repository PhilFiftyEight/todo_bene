import duckdb
import os
import logging
from sys import modules

# Détermine le nom du fichier log selon le contexte
log_file = "todo_bene_test.log" if "pytest" in modules else "todo_bene.log"

# Configuration du logging
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DuckDBConnectionManager:
    def __init__(self, db_path: str):
        self.conn = duckdb.connect(db_path)
        self._ensure_migration_table()
        self._run_migrations()

    def _ensure_migration_table(self):
        """Crée la table de suivi des migrations si elle n'existe pas."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                version INTEGER PRIMARY KEY,
                name TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def _run_migrations(self):
        """Lit et exécute les fichiers SQL de migration non appliqués."""
        migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")

        if not os.path.exists(migrations_dir):
            logger.warning(f"Dossier de migrations non trouvé : {migrations_dir}")
            return

        migration_files = sorted(
            [f for f in os.listdir(migrations_dir) if f.endswith(".sql")]
        )
        applied_versions = [
            row[0]
            for row in self.conn.execute("SELECT version FROM _migrations").fetchall()
        ]

        for filename in migration_files:
            try:
                version = int(filename.split("_")[0])
            except ValueError:
                continue

            if version not in applied_versions:
                logger.info(f"Application de la migration : {filename}")
                try:
                    with open(os.path.join(migrations_dir, filename), "r") as f:
                        sql = f.read()
                        self.conn.execute(sql)

                    self.conn.execute(
                        "INSERT INTO _migrations (version, name) VALUES (?, ?)",
                        [version, filename],
                    )
                    logger.info(f"Migration {filename} réussie.")
                except Exception as e:
                    logger.error(f"Erreur lors de la migration {filename} : {e}")
                    raise  # On stoppe tout si une migration échoue

    def get_connection(self):
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
