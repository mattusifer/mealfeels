#!/usr/bin/env python3

import subprocess
import logging
import os
from pathlib import Path

from livereload import Server

from mealfeels import create_app
from mealfeels.db import init_db

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s %(levelname)s %(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

os.environ |= {
    "TEXTBELT_API_KEY": "",
    "REPLY_WEBHOOK_URL": "",
    "PGHOST": "localhost",
    "PGUSER": "postgres",
    "PGPASSWORD": "password",
}

root_folder = (Path(__file__).parent.parent / "mealfeels").absolute()

subprocess.run(["docker", "compose", "up", "-d"], check=True)

app = create_app()
app.debug = True
app.config["LOCAL_DEV"] = True

logging.info("clearing db")
subprocess.run(["psql", "-f", "tests/clear.sql"], check=True)

with app.app_context():
    logging.info("initializing db")
    init_db()

logging.info("seeding db")
subprocess.run(["psql", "-f", "tests/seed.sql"], check=True)

logger.info(f"serving from {root_folder}")
server = Server(app.wsgi_app)
server.watch("mealfeels/static")
server.watch("mealfeels/templates")
server.serve(root=root_folder.as_posix())
