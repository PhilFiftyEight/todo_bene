import os
import shutil
import duckdb
from todo_bene.infrastructure.config import get_or_create_master_key, load_user_info

def migrate():
    # 1. Récupération des informations utilisateur
    _, db_path, _ = load_user_info()
    if not os.path.exists(db_path):
        print(f"❌ Erreur : La base {db_path} n'existe pas.")
        return

    new_db_path = db_path + ".encrypted"

    # 2. Récupération de la clé maître (64 caractères hex pour DuckDB)
    # Note : DuckDB attend souvent la clé en format hexadécimal pour ENCRYPTION_KEY
    master_key = get_or_create_master_key().decode('utf-8')

    print(f"🚀 Début de la migration : {db_path} -> {new_db_path}")

    try:
        # 3. Initialisation de la connexion
        #conn = duckdb.connect(db_path)
        conn = duckdb.connect()

        conn.execute("ATTACH ':memory:' as memory_db;")

        # 4. Chargement des extensions nécessaires au chiffrement
        # print("🔧 Chargement des extensions de sécurité...")
        conn.execute("INSTALL httpfs;")
        conn.execute("LOAD httpfs;")

        # 5. Attachement de la nouvelle base avec la clé de chiffrement
        # On utilise ENCRYPTION_KEY comme spécifié dans la doc 1.4
        print("🔐 Création de la base chiffrée...")
        conn.execute(f"ATTACH '{new_db_path}' AS enc_db (ENCRYPTION_KEY '{master_key}');")


        # 6. Transfert des données
        conn.execute(f"ATTACH '{db_path}' AS unencrypted;")
        conn.execute(f"USE unencrypted;")
        conn.execute(f"COPY FROM DATABASE unencrypted TO enc_db;")

        # 7. Fermeture des bases
        conn.execute("USE memory_db")
        conn.execute("DETACH enc_db;")
        conn.execute("DETACH unencrypted;")
        conn.close()
        print("✅ Migration des données terminée avec succès.")

        # 8. Remplacement définitif (Bascule)
        backup_path = db_path + ".bak"
        print(f"🔄 Mise en place de la nouvelle base...")

        if os.path.exists(backup_path):
            os.remove(backup_path)

        shutil.move(db_path, backup_path)
        shutil.move(new_db_path, db_path)

        print(f"\n✨ Félicitations ! Ta base est maintenant chiffrée.")
        print(f"📂 Ancienne base : {backup_path}")
        print(f"🔒 Base active   : {db_path}")

    except Exception as e:
        print(f"❌ Erreur fatale lors de la migration : {e}")
        if os.path.exists(new_db_path):
            os.remove(new_db_path)
        raise

if __name__ == "__main__":
    migrate()
