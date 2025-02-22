import functools
import secrets
from random import randint
import textwrap
import os
import logging

from flask import (
    Blueprint,
    flash,
    g,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

from mealfeels.db import get_db
from mealfeels.textbelt import send_message

bp = Blueprint("auth", __name__, url_prefix="/auth")

logger = logging.getLogger(__name__)

TOKEN_LENGTH = 64


@bp.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        raw_phone_number = request.form["phone"]
        error = None

        if not raw_phone_number:
            error = "Phone number is required."

        try:
            phone = phonenumbers.format_number(
                phonenumbers.parse(raw_phone_number, "US"),
                phonenumbers.PhoneNumberFormat.E164,
            )
        except NumberParseException as e:
            error = f"Error parsing phone number: {e}"

        if error is None:
            verification_code = str(randint(100000, 999999))
            new_token = secrets.token_urlsafe(TOKEN_LENGTH)

            db = get_db()
            cur = db.cursor()
            cur.execute(
                textwrap.dedent(
                    """\
                    INSERT INTO phones (phone, token, verification_code)
                    VALUES (%(phone)s, %(token)s, %(verification_code)s)
                    ON CONFLICT (phone) DO UPDATE
                    SET verification_code = %(verification_code)s
                    RETURNING token
                    """
                ),
                {
                    "phone": phone,
                    "token": new_token,
                    "verification_code": verification_code,
                },
            )
            db.commit()

            token = cur.fetchone()[0]

            send_message(
                phone,
                current_app.config["TEXTBELT_API_KEY"],
                f"Your Mealfeels verification code is {verification_code}.",
            )

            return redirect(url_for("auth.verify", phone=phone, token=token))

        logger.error(error)
        flash(error)

    return render_template("auth/login.html")


@bp.route("/verify", methods=("GET", "POST"))
def verify():
    if request.method == "POST":
        phone = request.args.get("phone")
        token = request.args.get("token")
        verification_code = request.form["verification_code"]

        if phone is None:
            logger.warn("verify url accessed without the phone param, redirecting")
            return redirect(url_for("auth.login"))

        error = None
        if verification_code is None:
            error = "Verification code is required"

        if error is None:
            db = get_db()
            cur = db.cursor()

            cur.execute(
                "SELECT id, verification_code FROM phones WHERE phone = %s",
                (phone,),
            )
            phone_id, actual_verification_code = cur.fetchone()

            if actual_verification_code != verification_code:
                error = "Invalid verification code"
            else:
                cur.execute(
                    "UPDATE phones SET verified=true WHERE phone = %s",
                    (phone,),
                )
                db.commit()

                send_message(
                    phone,
                    current_app.config["TEXTBELT_API_KEY"],
                    "👋 Welcome to Mealfeels. Respond to this text to start tracking.",
                    token=token,
                    reply_webhook_url=current_app.config["REPLY_WEBHOOK_URL"],
                )

                session.clear()
                session["phone_id"] = phone_id
                return redirect(url_for("home.symptoms"))

        flash(error)

    return render_template("auth/verify.html")


@bp.before_app_request
def load_logged_in_phone():
    if current_app.config.get("LOCAL_DEV"):
        phone_id = 1
    else:
        phone_id = session.get("phone_id")

    if phone_id is None:
        g.phone = None
    else:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM phones WHERE id = %s", (phone_id,))
        row = cur.fetchone()
        if row is not None:
            g.phone = row
        else:
            logger.warn(f"no phone found for logged in phone_id: {phone_id}")
            g.phone = None


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.phone is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view
