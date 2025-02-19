import os
import logging
from dataclasses import dataclass
from enum import Enum, auto

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
)
from werkzeug.exceptions import abort
from werkzeug.security import check_password_hash

from mealfeels.db import get_db
from mealfeels.textbelt import verify_request

bp = Blueprint("tracking", __name__, url_prefix="/tracking")

logger = logging.getLogger(__name__)


class MessageType(Enum):
    FOOD_DRINK = auto()
    BM = auto()
    FEEL = auto()
    UNKNOWN = auto()


class ParsedMessage:
    def __init__(self, message: str):
        message = message.strip()

        if message == "":
            self.message_type = MessageType.UNKNOWN
            return

        identifier = message.split()[0].lower()
        self.description = " ".join(message.split()[1:])

        if identifier in ["ate", "drank", "eat", "eating"]:
            self.message_type = MessageType.FOOD_DRINK
        elif identifier in ["bm"]:
            self.message_type = MessageType.BM
        elif identifier in ["felt", "feel", "feeling"]:
            self.message_type = MessageType.FEEL
        else:
            self.message_type = MessageType.UNKNOWN


def initiate(phone: str, key: str, reply_webhook_url: str):
    send_message(
        phone,
        key,
        "👋 Hello from mealfeels. Respond to this text to start tracking.",
        reply_webhook_url,
    )
    logger.info(f"successfully initiated text chain with {phone}")


@bp.route("/textbelt-webhook", methods=["POST"])
def textbelt_webhook():
    api_key = current_app.config["TEXTBELT_API_KEY"]

    # verify request according to textbelt specs
    # https://docs.textbelt.com/#verifying-the-webhook
    is_valid_request = verify_request(api_key, request)
    if not is_valid_request:
        return 400, "invalid request"

    request_body = request.json
    token = request_body.pop("data")
    phone = request_body["fromNumber"]
    text = request_body["text"].lower()

    logger.info(f"received request: {request_body}")

    db = get_db()
    cur = db.cursor()

    cur.execute("select token from phones where phone = %s", (phone,))

    hashed_token = cur.fetchone()[0]

    if not check_password_hash(hashed_token, token):
        logger.error("invalid token found in request")
        send_message(
            phone, api_key, "Error: invalid token. Re-register at mealfeels.com."
        )
        return "OK"

    parsed = ParsedMessage(text)
    if parsed.message_type == MessageType.UNKNOWN:
        send_message(phone, api_key, "Error: could not identify message type")
        return "OK"

    logger.debug("inserting into db")

    try:
        if parsed.message_type == MessageType.FOOD_DRINK:
            cur.execute(
                "INSERT INTO meals (phone, meal) VALUES (%s, %s)",
                (phone, parsed.description),
            )
        elif parsed.message_type == MessageType.FEEL:
            cur.execute(
                "INSERT INTO feels (phone, feel) VALUES (%s, %s)",
                (phone, parsed.description),
            )
        elif parsed.message_type == MessageType.BM:
            cur.execute(
                "INSERT INTO bms (phone, bm_description) VALUES (%s, %s)",
                (phone, parsed.description),
            )
        else:
            raise Exception(f"unsupported message type: {parsed.message_type}")

        cur.commit()
        send_message(phone, api_key, "👍")
    except Exception as e:
        send_message(phone, api_key, f"Error inserting into db: {e}")
    finally:
        cur.close()

    return "OK"
