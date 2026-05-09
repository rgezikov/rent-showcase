#!/bin/sh
set -e

uv run python manage.py migrate --noinput
uv run python manage.py loaddata listings/fixtures/categories.json

if [ "$DEBUG" = "False" ]; then
    uv run python manage.py collectstatic --noinput
fi

exec "$@"
