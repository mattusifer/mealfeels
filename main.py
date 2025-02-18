import os
import logging
from dataclasses import dataclass
from enum import Enum, auto

import requests
from flask import Flask, request
import psycopg2

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@dataclass
class Config:
    textbelt_api_key: str
    reply_webhook_url: str


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


def send_message(config: Config, phone: str, message: str):
    logger.debug(f"sending message to {phone} via textbelt: {message}")

    resp = requests.post(
        "https://textbelt.com/text",
        {
            "phone": phone,
            "message": message,
            "replyWebhookUrl": config.reply_webhook_url,
            "key": config.textbelt_api_key,
        },
    )
    resp.raise_for_status()
    resp_json = resp.json()

    if not resp_json["success"]:
        raise Exception(
            f"error from textbelt while sending message: {resp_json['error']}"
        )
    else:
        logger.debug(f"successful response from textbelt: {resp_json}")


def initiate(phone: str, key: str, reply_webhook_url: str):
    send_message(
        phone, key, reply_webhook_url, "ESSEN: Respond to this text to start tracking."
    )
    logger.info(f"successfully initiated text chain with {phone}")


def start_server(config: Config) -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def health():
        return "OK"

    @app.route("/textbelt-webhook", methods=["POST"])
    def textbelt_webhook():
        request_body = request.json
        logger.info(f"received request: {request_body}")

        phone = request_body.get("fromNumber")
        text = request_body.get("text").lower()

        parsed = ParsedMessage(text)
        if parsed.message_type == MessageType.UNKNOWN:
            send_message(config, phone, "Error: could not identify message type")
            return "OK"

        logger.debug("inserting into db")

        conn = psycopg2.connect()
        cur = conn.cursor()

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

            conn.commit()
            send_message(config, phone, "👍")
        except Exception as e:
            send_message(config, phone, f"Error inserting into db: {e}")
        finally:
            cur.close()
            conn.close()

        return "OK"

    return app


def main():
    textbelt_key = os.environ["TEXTBELT_API_KEY"]
    reply_webhook_url = os.environ["REPLY_WEBHOOK_URL"]
    phone = os.environ["PHONE"]

    config = Config(textbelt_key, reply_webhook_url)

    # initiate(phone, textbelt_key, reply_webhook_url)

    return start_server(config)
