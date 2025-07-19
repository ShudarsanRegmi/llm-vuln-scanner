# Windows PowerShell script to start all services
# Usage: .\start_all.ps1

Write-Host "Starting all services..." -ForegroundColor Green

# Set environment variable
$env:LLM_BACKEND = "llama"

# Start chatbot_api (LLM backend)
Write-Host "Starting chatbot_api (LLM backend) on port 8000..." -ForegroundColor Yellow
$chatbot_api = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "chatbot_api.main:app", "--reload", "--port", "8000" -RedirectStandardOutput "chatbot_api.log" -RedirectStandardError "chatbot_api_err.log" -PassThru -WindowStyle Hidden

# Wait a moment before starting next service
Start-Sleep -Seconds 2

# Start roberta_classifier_api
Write-Host "Starting roberta_classifier_api on port 9000..." -ForegroundColor Yellow
$roberta_classifier = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "roberta_classifier_api.main:app", "--reload", "--port", "9000" -RedirectStandardOutput "roberta_classifier_api.log" -RedirectStandardError "roberta_classifier_api_err.log" -PassThru -WindowStyle Hidden

# Wait a moment before starting next service
Start-Sleep -Seconds 2

# Start scanner_tool Flask app
Write-Host "Starting scanner_tool Flask app on port 8503..." -ForegroundColor Yellow
$scanner_tool = Start-Process -FilePath "python" -ArgumentList "scanner_tool/app.py" -RedirectStandardOutput "scanner_tool.log" -RedirectStandardError "scanner_tool_err.log" -PassThru -WindowStyle Hidden

# Wait a moment before starting next service
Start-Sleep -Seconds 2

# Start chatbot_ui Flask app
Write-Host "Starting chatbot_ui Flask app on port 8502..." -ForegroundColor Yellow
$chatbot_ui = Start-Process -FilePath "python" -ArgumentList "chatbot_ui/app.py" -RedirectStandardOutput "chatbot_ui.log" -RedirectStandardError "chatbot_ui_err.log" -PassThru -WindowStyle Hidden

# Show process info
Write-Host "---" -ForegroundColor Cyan
Write-Host "All services started." -ForegroundColor Green
Write-Host "chatbot_api PID: $($chatbot_api.Id) (log: chatbot_api.log)" -ForegroundColor White
Write-Host "roberta_classifier_api PID: $($roberta_classifier.Id) (log: roberta_classifier_api.log)" -ForegroundColor White
Write-Host "scanner_tool PID: $($scanner_tool.Id) (log: scanner_tool.log)" -ForegroundColor White
Write-Host "chatbot_ui PID: $($chatbot_ui.Id) (log: chatbot_ui.log)" -ForegroundColor White
Write-Host "---" -ForegroundColor Cyan

# Create a stop script
$stopScript = @"
# Stop all services
Write-Host "Stopping all services..." -ForegroundColor Red

try {
    Stop-Process -Id $($chatbot_api.Id) -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped chatbot_api (PID: $($chatbot_api.Id))" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop chatbot_api" -ForegroundColor Red
}

try {
    Stop-Process -Id $($roberta_classifier.Id) -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped roberta_classifier_api (PID: $($roberta_classifier.Id))" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop roberta_classifier_api" -ForegroundColor Red
}

try {
    Stop-Process -Id $($scanner_tool.Id) -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped scanner_tool (PID: $($scanner_tool.Id))" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop scanner_tool" -ForegroundColor Red
}

try {
    Stop-Process -Id $($chatbot_ui.Id) -Force -ErrorAction SilentlyContinue
    Write-Host "Stopped chatbot_ui (PID: $($chatbot_ui.Id))" -ForegroundColor Yellow
} catch {
    Write-Host "Could not stop chatbot_ui" -ForegroundColor Red
}

Write-Host "All services stopped." -ForegroundColor Green
"@

$stopScript | Out-File -FilePath "stop_all.ps1" -Encoding UTF8

Write-Host "To stop all services, run: .\stop_all.ps1" -ForegroundColor Green
Write-Host "Or manually stop using PIDs: $($chatbot_api.Id) $($roberta_classifier.Id) $($scanner_tool.Id) $($chatbot_ui.Id)" -ForegroundColor Green

# Keep the script running to show status
Write-Host "`nPress Ctrl+C to exit this monitoring script (services will continue running)" -ForegroundColor Magenta
try {
    while ($true) {
        Start-Sleep -Seconds 5
        $runningServices = 0
        
        if (Get-Process -Id $chatbot_api.Id -ErrorAction SilentlyContinue) { $runningServices++ }
        if (Get-Process -Id $roberta_classifier.Id -ErrorAction SilentlyContinue) { $runningServices++ }
        if (Get-Process -Id $scanner_tool.Id -ErrorAction SilentlyContinue) { $runningServices++ }
        if (Get-Process -Id $chatbot_ui.Id -ErrorAction SilentlyContinue) { $runningServices++ }
        
        Write-Host "$(Get-Date -Format 'HH:mm:ss') - $runningServices/4 services running" -ForegroundColor Gray
    }
} catch {
    Write-Host "`nMonitoring stopped. Services are still running." -ForegroundColor Green
}
