import logging
import textwrap
import json

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
import phonenumbers

from mealfeels.auth import login_required
from mealfeels.db import get_db

bp = Blueprint("home", __name__)

logger = logging.getLogger(__name__)


@bp.route("/symptoms")
@login_required
def symptoms():
    logged_in_phone_id = g.phone["id"]
    phone_number = phonenumbers.format_number(
        phonenumbers.parse(g.phone["phone"], "US"),
        phonenumbers.PhoneNumberFormat.NATIONAL,
    )

    db = get_db()
    cur = db.cursor()

    cur.execute(
        textwrap.dedent(
            """
            SELECT symptoms, EXTRACT(EPOCH FROM created_at) * 1000 AS created_at_millis
            FROM feels WHERE phone_id = %s
            ORDER BY 2
            """
        ),
        (logged_in_phone_id,),
    )
    symptoms = list(cur.fetchall())

    cur.execute(
        textwrap.dedent(
            """
            SELECT meal, EXTRACT(EPOCH FROM created_at) * 1000 AS created_at_millis
            FROM meals WHERE phone_id = %s
            """
        ),
        (logged_in_phone_id,),
    )
    meals = list(cur.fetchall())

    if g.phone["public_key"] is not None:
        # these are encrypted, send them as hex encoded srings
        symptoms = [(symptom.hex(), created_at) for symptom, created_at in symptoms]
        meals = [(meal.hex(), created_at) for meal, created_at in meals]
    else:
        # these are not encrypted, simply decode the strings
        symptoms = [
            (json.loads(symptom.tobytes().decode()), created_at)
            for symptom, created_at in symptoms
        ]
        meals = [(meal.tobytes().decode(), created_at) for meal, created_at in meals]

    return render_template(
        "home/symptoms.html",
        phone_number=phone_number,
        symptoms=symptoms,
        meals=meals,
    )
