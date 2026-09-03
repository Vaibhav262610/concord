# Show all tables in CONCORD database

Write-Host "`n=== CONCORD Database Tables ===" -ForegroundColor Green
Write-Host ""

# List all tables
docker-compose exec -T postgres psql -U concord -d concord -c "\dt"

Write-Host "`n=== Row Counts ===" -ForegroundColor Yellow
Write-Host ""

# Get row count for each table
$tables = @(
    "merchants",
    "agents", 
    "customers",
    "policies",
    "agent_requests",
    "decisions",
    "customer_contacts",
    "audit_logs",
    "delayed_actions"
)

foreach ($table in $tables) {
    $count = docker-compose exec -T postgres psql -U concord -d concord -t -c "SELECT COUNT(*) FROM $table;" 2>$null
    if ($count) {
        Write-Host "  $table : $($count.Trim()) rows" -ForegroundColor Cyan
    }
}

Write-Host ""
