FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# Run migrations, seed data, then start server
CMD ["sh", "-c", "\
    python manage.py migrate && \
    python manage.py seed_data && \
    python manage.py runserver 0.0.0.0:8000 \
"]
