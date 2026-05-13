#!/bin/sh
set -e

uv run python manage.py migrate --noinput
uv run python manage.py loaddata listings/fixtures/categories.json

# Set Sites framework domain from ALLOWED_HOSTS (used in password reset emails)
uv run python manage.py shell -c "
from django.contrib.sites.models import Site
import os
hosts = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')]
domain = next((h for h in hosts if h not in ('localhost', '127.0.0.1', '')), 'localhost')
Site.objects.filter(pk=1).update(domain=domain, name='Rent Showcase')
"

if [ "$DEBUG" = "False" ]; then
    uv run python manage.py collectstatic --noinput
fi

exec "$@"
