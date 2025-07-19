@echo off
echo Starting all services...

REM Set environment variable
set LLM_BACKEND=llama

REM Start chatbot_api (LLM backend)
echo Starting chatbot_api (LLM backend) on port 8000...
start "chatbot_api" cmd /c "python -m uvicorn chatbot_api.main:app --reload --port 8000 > chatbot_api.log 2>&1"

REM Wait a moment before starting next service
timeout /t 2 /nobreak >nul

REM Start roberta_classifier_api
echo Starting roberta_classifier_api on port 9000...
start "roberta_classifier_api" cmd /c "python -m uvicorn roberta_classifier_api.main:app --reload --port 9000 > roberta_classifier_api.log 2>&1"

REM Wait a moment before starting next service
timeout /t 2 /nobreak >nul

REM Start scanner_tool Flask app
echo Starting scanner_tool Flask app on port 8503...
start "scanner_tool" cmd /c "python scanner_tool/app.py > scanner_tool.log 2>&1"

REM Wait a moment before starting next service
timeout /t 2 /nobreak >nul

REM Start chatbot_ui Flask app
echo Starting chatbot_ui Flask app on port 8502...
start "chatbot_ui" cmd /c "python chatbot_ui/app.py > chatbot_ui.log 2>&1"

echo ---
echo All services started in separate windows.
echo Check the individual command windows for process status.
echo Log files: chatbot_api.log, roberta_classifier_api.log, scanner_tool.log, chatbot_ui.log
echo ---
echo To stop all services, close the individual command windows or use Task Manager.
echo.
echo Services:
echo - chatbot_api: http://localhost:8000
echo - roberta_classifier_api: http://localhost:9000
echo - scanner_tool: http://localhost:8503
echo - chatbot_ui: http://localhost:8502
echo.
pause
