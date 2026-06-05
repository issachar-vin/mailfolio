import smtplib
from email.message import EmailMessage


class GmailMailer:
    _SMTP_HOST = "smtp.gmail.com"
    _SMTP_PORT = 587

    def __init__(self, user: str, app_password: str) -> None:
        self._user = user
        self._app_password = app_password

    def send(self, *, to: str, subject: str, body: str, reply_to: str | None = None) -> None:
        msg = EmailMessage()
        msg["From"] = self._user
        msg["To"] = to
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.set_content(body)

        with smtplib.SMTP(self._SMTP_HOST, self._SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self._user, self._app_password)
            smtp.send_message(msg)
