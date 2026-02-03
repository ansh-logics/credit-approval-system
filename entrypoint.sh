#!/bin/sh
set -e

echo "Waiting for Postgres to be ready..."
until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" >/dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Postgres is up - continuing."

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Running initial data ingestion (if available)..."
python manage.py ingest_data || echo "Data ingestion command failed or not present, continuing."

echo "Starting Django server..."
exec "$@"

