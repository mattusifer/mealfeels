from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from mealfeels.auth import login_required

bp = Blueprint("home", __name__)


@bp.route("/")
@login_required
def index():
    return render_template("home/index.html")
