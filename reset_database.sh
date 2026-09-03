#!/bin/bash
# Reset the database for a clean start

echo "Stopping backend container..."
docker-compose stop backend

echo "Dropping and recreating database..."
docker-compose exec -T postgres psql -U concord -d postgres -c "DROP DATABASE IF EXISTS concord;"
docker-compose exec -T postgres psql -U concord -d postgres -c "CREATE DATABASE concord;"

echo "Starting backend container..."
docker-compose up -d backend

echo "Waiting for migrations to complete..."
sleep 10

echo "Checking backend logs..."
docker-compose logs --tail=20 backend

echo ""
echo "Done! Check if backend is running:"
echo "  docker-compose ps backend"
echo "  curl http://localhost:8000/health"
