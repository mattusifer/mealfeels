import logging
import textwrap

from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort
import phonenumbers

from mealfeels.auth import login_required
from mealfeels.db import get_db

bp = Blueprint("home", __name__)

logger = logging.getLogger(__name__)


@bp.route("/")
@login_required
def index():
    logged_in_phone_id = g.phone[0]
    phone_number = phonenumbers.format_number(
        phonenumbers.parse(g.phone[1], "US"),
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

    return render_template(
        "home/index.html", phone_number=phone_number, symptoms=symptoms, meals=meals
    )
