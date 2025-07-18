#!/bin/bash

echo "Starting RoBERTa Classifier API..."
echo "Model files check:"
ls -la ../model/ | grep -E "(config.json|model.safetensors|tokenizer_config.json|vocab.json|merges.txt)"

echo "
Starting server on port 9001..."
echo "API will be available at: http://localhost:9001"
echo "Health check: http://localhost:9001/health"
echo "API documentation: http://localhost:9001/docs"
echo "
Press Ctrl+C to stop the server"
echo "================================================"

python main.py

