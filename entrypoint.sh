#!/bin/sh

# Exit immediately if a commands exits with a non-zero status.
set -e

# Run Django migrations
python manage.py migrate

# Collect static files (optional)
# python manage.py collectstatic --noinput

# Start the Django server
exec "$@"
