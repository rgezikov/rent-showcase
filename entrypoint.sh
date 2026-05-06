#!/bin/sh
set -e

uv run python manage.py migrate --noinput

if [ "$DEBUG" = "False" ]; then
    uv run python manage.py collectstatic --noinput
fi

exec "$@"
