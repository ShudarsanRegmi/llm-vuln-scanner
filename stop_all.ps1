# Stop all services
Write-Host "Stopping all services..." -ForegroundColor Red

try {
    Stop-Process -Id  -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped chatbot_api (PID: )" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop chatbot_api" -ForegroundColor Red
}

try {
    Stop-Process -Id  -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped roberta_classifier_api (PID: )" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop roberta_classifier_api" -ForegroundColor Red
}

try {
    Stop-Process -Id  -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped scanner_tool (PID: )" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop scanner_tool" -ForegroundColor Red
}

try {
    Stop-Process -Id  -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped chatbot_ui (PID: )" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop chatbot_ui" -ForegroundColor Red
}

Write-Host "All services stopped." -ForegroundColor Green
