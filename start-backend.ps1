# Start CONCORD backend with the new fixed image
Write-Host "Starting CONCORD backend..." -ForegroundColor Cyan
docker-compose up -d backend

Write-Host ""
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Checking backend logs:" -ForegroundColor Cyan
docker-compose logs backend --tail 20

Write-Host ""
Write-Host "[OK] Backend started! Check above for any errors." -ForegroundColor Green
Write-Host "[OK] API should be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "[OK] API docs at: http://localhost:8000/docs" -ForegroundColor Green
