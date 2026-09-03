# Quick script to access PostgreSQL database

Write-Host "Connecting to CONCORD database..." -ForegroundColor Green
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  \dt              - List all tables" -ForegroundColor Cyan
Write-Host "  \d table_name    - Describe a table" -ForegroundColor Cyan
Write-Host "  \l               - List all databases" -ForegroundColor Cyan
Write-Host "  \q               - Quit" -ForegroundColor Cyan
Write-Host ""
Write-Host "Example queries:" -ForegroundColor Yellow
Write-Host "  SELECT * FROM merchants;" -ForegroundColor Cyan
Write-Host "  SELECT * FROM agents;" -ForegroundColor Cyan
Write-Host "  SELECT * FROM customers;" -ForegroundColor Cyan
Write-Host ""

docker-compose exec postgres psql -U concord -d concord
