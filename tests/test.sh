#!/bin/bash
set -ex

export TEXTBELT_API_KEY=''
export REPLY_WEBHOOK_URL=''
export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=password

# cd to the root of the repo
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path" && cd ..

# setup database
flask --app mealfeels init-db
psql -f tests/seed.sql

# start app
MEALFEELS_DEV_PHONE_ID=1 \
  flask --app mealfeels run --debug
