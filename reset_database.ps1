# Reset the database for a clean start

Write-Host "Stopping backend container..." -ForegroundColor Yellow
docker-compose stop backend

Write-Host "`nDropping and recreating database..." -ForegroundColor Yellow
docker-compose exec -T postgres psql -U concord -d postgres -c "DROP DATABASE IF EXISTS concord;"
docker-compose exec -T postgres psql -U concord -d postgres -c "CREATE DATABASE concord;"

Write-Host "`nStarting backend container..." -ForegroundColor Yellow
docker-compose up -d backend

Write-Host "`nWaiting for migrations to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`nChecking backend logs..." -ForegroundColor Yellow
docker-compose logs --tail=20 backend

Write-Host "`n" -ForegroundColor Green
Write-Host "Done! Check if backend is running:" -ForegroundColor Green
Write-Host "  docker-compose ps backend" -ForegroundColor Cyan
Write-Host "  curl http://localhost:8000/health" -ForegroundColor Cyan
