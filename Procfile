release: bash build.sh
web: gunicorn --workers 4 --bind 0.0.0.0:$PORT dashboard.api:app --timeout 120