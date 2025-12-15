release: cd frontend && npm install && npm run build
web: gunicorn --workers 4 --bind 0.0.0.0:$PORT dashboard.api:app --timeout 120