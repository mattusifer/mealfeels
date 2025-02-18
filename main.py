import os
import logging

import requests
from flask import Flask, request
import psycopg2

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def initiate(phone: str, key: str, reply_webhook_url: str):
    resp = requests.post(
        "https://textbelt.com/text",
        {
            "phone": phone,
            "message": "ESSEN: Respond to this text to start tracking.",
            "replyWebhookUrl": reply_webhook_url,
            "key": key,
        },
    )
    resp.raise_for_status()
    resp_json = resp.json()

    if not resp_json["success"]:
        logger.error(f"error from textbelt during initialization: {resp_json['error']}")
        exit(1)

    logger.info(f"successfully initiated text chain with {phone}")


def start_server() -> Flask:
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

        if not text.startswith("ate") and not text.startswith("feel"):
            logger.info(f"I dont know what to do with this message: {text}")
            return "OK"
        else:
            logger.info("inserting into db")

        conn = psycopg2.connect()
        cur = conn.cursor()

        try:
            if text.startswith("ate"):
                cur.execute(
                    "INSERT INTO meals (phone, meal) VALUES (%s, %s)",
                    (phone, text.removeprefix("ate")),
                )
            elif text.startswith("feel"):
                cur.execute(
                    "INSERT INTO feels (phone, feel) VALUES (%s, %s)",
                    (phone, text.removeprefix("feel")),
                )
            conn.commit()
        finally:
            cur.close()
            conn.close()

        return "OK"

    return app


def main():
    textbelt_key = os.environ["TEXTBELT_API_KEY"]
    reply_webhook_url = os.environ["REPLY_WEBHOOK_URL"]
    phone = os.environ["PHONE"]

    # initiate(phone, textbelt_key, reply_webhook_url)

    return start_server()
