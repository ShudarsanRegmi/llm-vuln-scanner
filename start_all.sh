#!/bin/bash

# Start chatbot_api (LLM backend)
echo "Starting chatbot_api (LLM backend) on port 8000..."
export LLM_BACKEND=llama
uvicorn chatbot_api.main:app --reload --port 8000 > chatbot_api.log 2>&1 &
CHATBOT_API_PID=$!

# Start fake_classifier_api
sleep 2
echo "Starting fake_classifier_api on port 9000..."
uvicorn fake_classifier_api.main:app --reload --port 9000 > fake_classifier_api.log 2>&1 &
FAKE_CLASSIFIER_PID=$!

# Start scanner_tool Flask app
sleep 2
echo "Starting scanner_tool Flask app on port 8503..."
python3 scanner_tool/app.py > scanner_tool.log 2>&1 &
SCANNER_TOOL_PID=$!

# Start chatbot_ui Flask app
sleep 2
echo "Starting chatbot_ui Flask app on port 8502..."
python3 chatbot_ui/app.py > chatbot_ui.log 2>&1 &
CHATBOT_UI_PID=$!

# Show process info
echo "---"
echo "All services started."
echo "chatbot_api PID: $CHATBOT_API_PID (log: chatbot_api.log)"
echo "fake_classifier_api PID: $FAKE_CLASSIFIER_PID (log: fake_classifier_api.log)"
echo "scanner_tool PID: $SCANNER_TOOL_PID (log: scanner_tool.log)"
echo "chatbot_ui PID: $CHATBOT_UI_PID (log: chatbot_ui.log)"
echo "---"
echo "To stop all, run: kill $CHATBOT_API_PID $FAKE_CLASSIFIER_PID $SCANNER_TOOL_PID $CHATBOT_UI_PID" 