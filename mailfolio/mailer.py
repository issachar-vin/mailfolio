import smtplib
from email.mime.multipart import MIMEMultipart
from typing import Protocol


class Mailer(Protocol):
    def send(self, *, to: str, msg: MIMEMultipart) -> None: ...


class GmailMailer:
    _SMTP_HOST = "smtp.gmail.com"
    _SMTP_PORT = 587

    def __init__(self, user: str, app_password: str) -> None:
        self._user = user
        self._app_password = app_password

    def send(self, *, to: str, msg: MIMEMultipart) -> None:
        msg["From"] = self._user
        msg["To"] = to

        with smtplib.SMTP(self._SMTP_HOST, self._SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self._user, self._app_password)
            smtp.send_message(msg)
