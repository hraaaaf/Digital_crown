import logging
import smtplib
from email.message import EmailMessage
from html import escape

from backend.config import settings

logger = logging.getLogger("digital_crown.email_service")


class EmailService:
    """SMTP transactionnel avec mode no-op si la configuration est absente."""

    @property
    def is_configured(self) -> bool:
        return bool(settings.SMTP_HOST and settings.SMTP_FROM_EMAIL)

    def send_email(self, to_email: str, subject: str, text: str, html: str | None = None) -> bool:
        if not to_email:
            logger.warning("Email ignore: destinataire vide pour '%s'", subject)
            return False

        if not self.is_configured:
            logger.warning(
                "SMTP non configure. Email simule vers %s: %s",
                to_email,
                subject,
            )
            return True

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message.set_content(text)
        if html:
            message.add_alternative(html, subtype="html")

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                smtp.send_message(message)
            logger.info("Email envoye a %s: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.error("Echec envoi email a %s: %s", to_email, exc)
            return False

    def send_signup_received(self, to_email: str, full_name: str | None) -> bool:
        display_name = full_name or "Docteur"
        text = (
            f"Bonjour {display_name},\n\n"
            "Votre demande d'acces a Digital Crown a bien ete recue. "
            "Notre equipe la verifiera et vous recevrez un email des activation.\n\n"
            f"Support: {settings.SUPPORT_EMAIL}"
        )
        html = f"""
        <p>Bonjour {escape(display_name)},</p>
        <p>Votre demande d'acces a <strong>Digital Crown</strong> a bien ete recue.</p>
        <p>Notre equipe la verifiera et vous recevrez un email des activation.</p>
        <p>Support: <a href="mailto:{escape(settings.SUPPORT_EMAIL)}">{escape(settings.SUPPORT_EMAIL)}</a></p>
        """
        return self.send_email(to_email, "Demande d'acces Digital Crown recue", text, html)

    def send_admin_signup_notice(self, client_email: str, full_name: str | None) -> bool:
        admin_email = settings.ADMIN_NOTIFICATION_EMAIL or settings.SMTP_FROM_EMAIL
        text = (
            "Nouvelle demande d'inscription Digital Crown.\n\n"
            f"Nom: {full_name or '-'}\n"
            f"Email: {client_email}\n"
            f"Panneau superadmin: {settings.APP_PUBLIC_URL.rstrip('/')}/super-admin"
        )
        html = f"""
        <p>Nouvelle demande d'inscription Digital Crown.</p>
        <ul>
          <li><strong>Nom:</strong> {escape(full_name or '-')}</li>
          <li><strong>Email:</strong> {escape(client_email)}</li>
        </ul>
        <p><a href="{escape(settings.APP_PUBLIC_URL.rstrip('/'))}/super-admin">Ouvrir le panneau superadmin</a></p>
        """
        return self.send_email(admin_email, "Nouvelle inscription Digital Crown", text, html)

    def send_account_activated(self, to_email: str, full_name: str | None, expires_at) -> bool:
        display_name = full_name or "Docteur"
        expiry = expires_at.strftime("%d/%m/%Y") if expires_at else "non definie"
        login_url = f"{settings.APP_PUBLIC_URL.rstrip('/')}/login"
        text = (
            f"Bonjour {display_name},\n\n"
            f"Votre compte Digital Crown est active. Votre licence d'essai est valable jusqu'au {expiry}.\n"
            f"Connexion: {login_url}\n\n"
            f"Support: {settings.SUPPORT_EMAIL}"
        )
        html = f"""
        <p>Bonjour {escape(display_name)},</p>
        <p>Votre compte <strong>Digital Crown</strong> est active.</p>
        <p>Votre licence d'essai est valable jusqu'au <strong>{escape(expiry)}</strong>.</p>
        <p><a href="{escape(login_url)}">Se connecter</a></p>
        <p>Support: <a href="mailto:{escape(settings.SUPPORT_EMAIL)}">{escape(settings.SUPPORT_EMAIL)}</a></p>
        """
        return self.send_email(to_email, "Votre compte Digital Crown est active", text, html)

    def send_license_expiry_notice(self, to_email: str, full_name: str | None, expires_at, days_left: int) -> bool:
        display_name = full_name or "Docteur"
        expiry = expires_at.strftime("%d/%m/%Y") if expires_at else "bientot"
        text = (
            f"Bonjour {display_name},\n\n"
            f"Votre licence Digital Crown expire dans {days_left} jour(s), le {expiry}.\n"
            f"Contactez le support pour renouveler: {settings.SUPPORT_EMAIL}"
        )
        html = f"""
        <p>Bonjour {escape(display_name)},</p>
        <p>Votre licence Digital Crown expire dans <strong>{days_left} jour(s)</strong>, le <strong>{escape(expiry)}</strong>.</p>
        <p>Contactez le support pour renouveler: <a href="mailto:{escape(settings.SUPPORT_EMAIL)}">{escape(settings.SUPPORT_EMAIL)}</a></p>
        """
        return self.send_email(to_email, "Expiration prochaine de votre licence Digital Crown", text, html)


email_service = EmailService()
