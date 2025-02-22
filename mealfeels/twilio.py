import logging
from time import sleep

from twilio.rest import Client

logger = logging.getLogger(__name__)


def send_message(
    phone: str,
    twilio_account_sid: str,
    twilio_auth_token: str,
    twilio_number: str,
    message: str,
    token: str | None = None,
    reply_webhook_url: str | None = None,
):
    client = Client(twilio_account_sid, twilio_auth_token)
    client.http_client.logger.setLevel(logging.INFO)

    message = client.messages.create(to=phone, from_=twilio_number, body=message)

    while True:
        status = client.messages.get(message.sid).status
        if status == "delivered":
            logger.debug(f"message sent successfully")
            break
        if status != "queued":
            logger.warn(f"unexpected status: {status}")
            break

        logger.info("message still queued")
        sleep(1)


def verify_request(api_key, request):
    pass
