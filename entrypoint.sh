#! /bin/bash

echo assets_view_logs > assets_views.log
echo requests_logs > requests.log

python3 manage.py makemigrations --no-input

python3 manage.py migrate --no-input

python3 manage.py collectstatic --no-input

exec gunicorn cloud_assets.wsgi:application -b 0.0.0.0:8000 --reload
