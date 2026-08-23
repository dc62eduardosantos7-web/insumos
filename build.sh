#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
DATABASE_URL="" DEBUG=True python manage.py test
python manage.py collectstatic --no-input
python manage.py migrate
