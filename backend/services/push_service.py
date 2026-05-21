import logging
from sqlalchemy.orm import Session
from firebase_admin import messaging
from backend import models

logger = logging.getLogger(__name__)


def send_push_to_employer(db: Session, employer_id: int, title: str, body: str) -> int:
    """Envoie un push FCM multicast à tous les devices enregistrés pour cet employer."""
    tokens_rows = db.query(models.DeviceToken).filter(
        models.DeviceToken.employer_id == employer_id
    ).all()
    if not tokens_rows:
        return 0

    token_list = [t.fcm_token for t in tokens_rows]
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=token_list,
            android=messaging.AndroidConfig(priority="high"),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(aps=messaging.Aps(sound="default"))
            ),
        )
        response = messaging.send_each_for_multicast(message)
        if response.failure_count > 0:
            invalid = [
                token_list[i]
                for i, r in enumerate(response.responses)
                if not r.success
            ]
            if invalid:
                db.query(models.DeviceToken).filter(
                    models.DeviceToken.fcm_token.in_(invalid)
                ).delete(synchronize_session=False)
                db.commit()
        return response.success_count
    except Exception as e:
        logger.error("FCM send failed for employer %s: %s", employer_id, e)
        return 0
