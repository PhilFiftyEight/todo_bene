import os
from sys import modules
import logging

import duckdb

from todo_bene.infrastructure.config import get_or_create_master_key

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
    def __init__(self, db_path: str, read_only: bool = False):
        self.db_path = db_path
        self.access_mode = 'READ_ONLY' if read_only else 'READ_WRITE'
        self.conn = None


    def __enter__(self):
        try:
            # Récupération de la clé
            master_key = get_or_create_master_key().decode('utf-8')
            # Ouverture de la connexion ⚠️ Cette méthode ne fonctionne pas avec la base chiffrée
            try:
                self.conn = duckdb.connect(
                    self.db_path,
                    config={
                        'access_mode': self.access_mode,
                    }
                )
            except duckdb.Error:
                self.conn = duckdb.connect()
                self.conn.execute("LOAD httpfs;")
                # ATTACH 'encrypted.db' AS enc_db (ACCESS_MODE, ENCRYPTION_KEY 'quack_quack') <<< voir la doc
                self.conn.execute(f"ATTACH '{self.db_path}' AS enc_db ({self.access_mode}, ENCRYPTION_KEY '{master_key}');")
                self.conn.execute("USE enc_db;")

            # Exécution des migrations
            if self.access_mode == 'READ_WRITE':
                self._ensure_migration_table()
                self._run_migrations()
            else:
                logger.info(f"Connexion DuckDB établie en mode READ_ONLY pour {self.db_path}")

            return self.conn
        except duckdb.Error:
            # On log l'erreur technique pour le développeur
            logger.error("Erreur fatale lors de l'ouverture de la base : (la clé est incorrecte ou manquante)")

            # On affiche un message clair pour l'utilisateur
            print("\n[ERREUR CRITIQUE] Impossible d'accéder à vos données.")
            print("Vérifiez que votre trousseau d'accès est déverrouillé.")
            print("Si le problème persiste, votre clé de chiffrement est peut-être invalide.")

            # On arrête proprement l'exécution
            raise SystemExit(1)


    def __exit__(self, exc_type, exc_val, traceback):
        try: # if bdd encrypted
            self.conn.execute("ATTACH ':memory:' as memory_db;")
            self.conn.execute("USE memory_db;")
            self.conn.execute("DETACH enc_db;")
        except duckdb.Error:
            logger.info(f"MANAGER EXIT : La base n'est pas cryptée, fermeture avec conn.close()")
        finally:
            self.close()


    def get_connection(self):
        return self.conn


    def close(self):
        if self.conn:
            self.conn.close()


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
                    logger.error(f"Erreur lors de la migration {filename}")
                    raise  # On stoppe tout si une migration échoue
