import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from dotenv import load_dotenv
from todo_bene.domain.entities.todo import Todo
from todo_bene.infrastructure.config import decrypt_value

logger = logging.getLogger(__name__)

def send_email_notification(recipient: str, todos: List[Todo], subject: str) -> bool:
    """
    Envoie une notification par email en utilisant des identifiants chiffrés dans le .env.
    """
    load_dotenv()
    # 1. Récupération des secrets chiffrés
    encrypted_user = os.getenv("SMTP_USER")
    encrypted_pass = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not encrypted_user or not encrypted_pass:
        logger.error("Identifiants SMTP chiffrés manquants dans l'environnement.")
        return False

    try:
        # 2. Déchiffrement avec la clé Fernet
        smtp_user = decrypt_value(encrypted_user)
        smtp_password = decrypt_value(encrypted_pass)

        # 3. Construction du message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Todo Bene <{smtp_user}>"
        msg["To"] = recipient

        # text_content = "Tes tâches :\n" + "\n".join([f"- {t.title}" for t in todos])
        # html_items = "".join([f"<li>{t.title}</li>" for t in todos])
        # html_content = f"<html><body><h2>Tes tâches à faire</h2><ul>{html_items}</ul></body></html>"

        # Dans notifications.py, la boucle devient :
        text_items = [f"[{t['time']}] {t['title']}\n   {t['description']}\n-------------------------" for t in todos]
        text_content = "Tes tâches :\n\n" + "\n\n".join(text_items)

        # Construction du contenu HTML avec séparation propre
        html_items = "".join([
            f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <span style="color: #666; font-weight: bold;">[{t['time']}]</span>
                <strong style="font-size: 1.1em;">{t['title']}</strong><br>
                <p style="margin: 5px 0 0 0; color: #333;">{t['description']}</p>
            </div>
            """
            for t in todos
        ])
        html_content = f"""
        <html>
            <body style="font-family: sans-serif; line-height: 1.5;">
                <h2 style="color: #2c3e50;">📋 Récapitulatif de tes tâches</h2>
                {html_items}
            </body>
        </html>
        """

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # 4. Envoi sécurisé
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient, msg.as_string())

        logger.info(f"Email envoyé avec succès")
        return True

    except Exception as e:
        logger.error(f"Échec de l'envoi SMTP")
        return False
