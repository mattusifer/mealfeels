import logging
import hmac
import hashlib

import requests

logger = logging.getLogger(__name__)


def send_message(
    phone: str,
    textbelt_api_key: str,
    message: str,
    token: str | None = None,
    reply_webhook_url: str | None = None,
):
    logger.debug(f"sending message to {phone} via textbelt: {message}")

    params = {
        "phone": phone,
        "message": message,
        "key": textbelt_api_key,
        "webhookData": token,
    }
    if reply_webhook_url:
        params["replyWebhookUrl"] = reply_webhook_url

    resp = requests.post("https://textbelt.com/text", params)
    resp.raise_for_status()
    resp_json = resp.json()

    if not resp_json["success"]:
        raise Exception(
            f"error from textbelt while sending message: {resp_json['error']}"
        )
    else:
        logger.debug(f"successful response from textbelt: {resp_json}")


def verify_request(api_key, request):
    request_signature = request.headers["x-textbelt-signature"]
    request_timestamp = request.headers["x-textbelt-timestamp"]

    my_signature = hmac.new(
        api_key.encode("utf-8"),
        (request_timestamp + request.data.decode("utf-8")).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    is_valid = hmac.compare_digest(request_signature, my_signature)
    if not is_valid:
        logger.info(
            f"invalid request received: {request_signature=} {request_timestamp=} {request.text=}"
        )

    return is_valid
