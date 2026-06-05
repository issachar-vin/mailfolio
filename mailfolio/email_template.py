import html
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_contact_email(name: str, email: str, subject: str, message: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["Reply-To"] = email
    msg.attach(MIMEText(_plain(name, email, message), "plain"))
    msg.attach(MIMEText(_html(name, email, subject, message), "html"))
    return msg


def _plain(name: str, email: str, message: str) -> str:
    return (
        f"New contact form submission\n"
        f"===========================\n\n"
        f"From:    {name} <{email}>\n\n"
        f"{message}\n\n"
        f"---\n"
        f"Reply: mailto:{email}"
    )


def _html(name: str, email: str, subject: str, message: str) -> str:
    h_name = html.escape(name)
    h_email = html.escape(email)
    h_subject = html.escape(subject)
    h_message = html.escape(message)
    mailto = f"mailto:{urllib.parse.quote(email)}?subject={urllib.parse.quote('Re: ' + subject)}"

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4f4f4;padding:32px 0;">
  <tr>
    <td align="center">
      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;width:100%;background:#ffffff;border-radius:6px;overflow:hidden;border:1px solid #e0e0e0;">

        <!-- Header -->
        <tr>
          <td style="background:#1a1a2e;padding:24px 32px;">
            <p style="margin:0;color:#ffffff;font-size:17px;font-weight:bold;letter-spacing:0.3px;">
              New contact form submission
            </p>
          </td>
        </tr>

        <!-- Sender info -->
        <tr>
          <td style="padding:24px 32px 0 32px;border-bottom:1px solid #e8e8e8;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="padding-bottom:16px;">
                  <span style="display:block;color:#888888;font-size:11px;text-transform:uppercase;
                               letter-spacing:0.8px;margin-bottom:4px;">From</span>
                  <span style="color:#1a1a1a;font-size:15px;font-weight:600;">{h_name}</span>
                  <span style="color:#666666;font-size:14px;">&nbsp;&lt;{h_email}&gt;</span>
                </td>
              </tr>
              <tr>
                <td style="padding-bottom:24px;">
                  <span style="display:block;color:#888888;font-size:11px;text-transform:uppercase;
                               letter-spacing:0.8px;margin-bottom:4px;">Subject</span>
                  <span style="color:#1a1a1a;font-size:15px;">{h_subject}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Message body -->
        <tr>
          <td style="padding:28px 32px 32px 32px;">
            <p style="margin:0 0 12px 0;color:#888888;font-size:11px;text-transform:uppercase;
                      letter-spacing:0.8px;">Message</p>
            <p style="margin:0;color:#333333;font-size:15px;line-height:1.7;white-space:pre-wrap;">{h_message}</p>
          </td>
        </tr>

        <!-- Reply CTA -->
        <tr>
          <td style="padding:0 32px 32px 32px;">
            <table cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="background:#1a1a2e;border-radius:4px;">
                  <a href="{mailto}"
                     style="display:inline-block;padding:12px 24px;color:#ffffff;font-size:14px;
                            font-weight:600;text-decoration:none;letter-spacing:0.3px;">
                    Reply to {h_name}
                  </a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:16px 32px;background:#f9f9f9;border-top:1px solid #e8e8e8;">
            <p style="margin:0;color:#aaaaaa;font-size:12px;">Sent via your portfolio contact form</p>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""
