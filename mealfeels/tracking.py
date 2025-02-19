import os
import logging
from dataclasses import dataclass
from enum import Enum, auto
import re
import textwrap

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
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from werkzeug.exceptions import abort

from mealfeels.db import get_db
from mealfeels.textbelt import verify_request, send_message

bp = Blueprint("tracking", __name__, url_prefix="/tracking")

logger = logging.getLogger(__name__)


class MessageType(Enum):
    FOOD_DRINK = auto()
    BM = auto()
    FEEL = auto()
    SLEEP = auto()
    UNKNOWN = auto()


class ParsedMessage:
    def __init__(self, message: str):
        message = message.strip()

        if message == "":
            self.message_type = MessageType.UNKNOWN
            return

        identifier = message.split()[0].lower()
        self.description = " ".join(message.split()[1:])

        if identifier in ["ate", "drank", "drinking", "eat", "eating"]:
            self.message_type = MessageType.FOOD_DRINK
        elif identifier in ["bm"]:
            self.message_type = MessageType.BM
        elif identifier in ["slept"]:
            self.message_type = MessageType.SLEEP

            hours_regex = re.compile(r"([0-9]+) hour")
            matched = re.search(hours_regex, self.description)
            if matched:
                self.hours = int(matched[1])
            else:
                self.hours = 0
        elif identifier in ["felt", "feel", "feeling"]:
            self.message_type = MessageType.FEEL

            number_at_end = re.compile(r" ([0-9]+)$")

            self.symptoms = {}
            for symptom in self.description.split(","):
                matched = re.search(number_at_end, symptom)
                if matched:
                    magnitude = int(matched[1])
                    symptom = re.sub(number_at_end, "", symptom)
                else:
                    logger.warn(f"no magnitude found for {symptom=} in {message=}")
                    magnitude = None

                self.symptoms[symptom.strip()] = magnitude

        else:
            self.message_type = MessageType.UNKNOWN


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
    raw_phone_number = request_body["fromNumber"]
    text = request_body["text"].lower()

    try:
        phone = phonenumbers.format_number(
            phonenumbers.parse(raw_phone_number),
            phonenumbers.PhoneNumberFormat.E164,
        )
    except NumberParseException as e:
        logger.error(f"Error parsing phone number from textbelt: {e}")
        return f"Error parsing fromNumber: {e}", 400

    logger.info(f"received request: {request_body}")

    db = get_db()
    cur = db.cursor()

    cur.execute("select id, token from phones where phone = %s", (phone,))
    result = cur.fetchone()
    if result is None:
        send_message(
            phone,
            api_key,
            f"Number not recognized! Sorry for the inconvenience. Register at mealfeels.com.",
        )
        return "OK"

    phone_id, actual_token = result

    if actual_token != token:
        logger.error(f"invalid token found in request")
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
                "INSERT INTO meals (phone_id, meal) VALUES (%s, %s)",
                (phone_id, parsed.description),
            )
        elif parsed.message_type == MessageType.FEEL:
            for symptom, magnitude in parsed.symptoms.items():
                cur.execute(
                    textwrap.dedent(
                        """\
                        INSERT INTO feels (phone_id, full_description, symptom, magnitude)
                        VALUES (%s, %s, %s, %s)
                        """
                    ),
                    (phone_id, parsed.description, symptom, magnitude),
                )
        elif parsed.message_type == MessageType.BM:
            cur.execute(
                "INSERT INTO bms (phone_id, bm_description) VALUES (%s, %s)",
                (phone_id, parsed.description),
            )
        elif parsed.message_type == MessageType.SLEEP:
            cur.execute(
                "INSERT INTO sleeps (phone_id, description, hours) VALUES (%s, %s, %s)",
                (phone_id, parsed.description, parsed.hours),
            )
        else:
            raise Exception(f"unsupported message type: {parsed.message_type}")

        db.commit()
        send_message(phone, api_key, "👍")
    except Exception as e:
        send_message(phone, api_key, f"Error inserting into db: {e}")
    finally:
        cur.close()

    return "OK"
