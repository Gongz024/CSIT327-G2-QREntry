from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SendGridBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent_count = 0
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        for message in email_messages:
            # Support different formats of message.to
            to_emails = [addr for name, addr in message.to or []] if hasattr(message, 'to') else message.to
            email = Mail(
                from_email=message.from_email or settings.FROM_EMAIL,
                to_emails=to_emails,
                subject=message.subject,
                plain_text_content=message.body,
            )
            try:
                response = sg.send(email)

                # Log the full response for debugging
                logger.info(f"📨 SendGrid Response: Status {response.status_code}, Headers {response.headers}, Body: {response.body}")

                print(f"📨 SendGrid Response: Status {response.status_code}, Body: {response.body}")  # optional console output

                if response.status_code in [200, 202]:
                    sent_count += 1
                else:
                    logger.warning(f"⚠️ SendGrid returned non-success status: {response.status_code}")

            except Exception as e:
                logger.error(f"❌ SendGrid failed: {e}")
                if not self.fail_silently:
                    raise e

        return sent_count
