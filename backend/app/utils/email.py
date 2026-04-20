import logging

logger = logging.getLogger(__name__)


def send_verification_email(email: str, token: str) -> None:
    logger.info("Verification email to %s, token=%s", email, token)


def send_password_reset_email(email: str, token: str) -> None:
    logger.info("Password reset email to %s, token=%s", email, token)
