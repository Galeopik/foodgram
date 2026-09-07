FROM python:3.12

WORKDIR /app

COPY backend/requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY backend/ .

COPY data/ ./data/

CMD ["sh", "-c", "python manage.py migrate && python manage.py load_ingredients && python manage.py load_tags && python manage.py collectstatic --no-input && gunicorn --bind 0.0.0.0:8000 foodgram_backend.wsgi"]