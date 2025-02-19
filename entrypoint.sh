#!/bin/sh
set -ex

flask --app mealfeels init-db

gunicorn -b 0.0.0.0 -w 1 'mealfeels:create_app()'
