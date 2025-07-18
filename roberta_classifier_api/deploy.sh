#!/bin/bash

# RoBERTa Classifier API Deployment Script

echo "================================================"
echo "RoBERTa Classifier API Deployment"
echo "================================================"

# Check if model directory exists
if [ ! -d "../model" ]; then
    echo "Error: Model directory not found at ../model"
    echo "Please ensure the model files are in the correct location."
    exit 1
fi

# Check if required model files exist
required_files=("config.json" "model.safetensors" "tokenizer_config.json" "vocab.json" "merges.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "../model/$file" ]; then
        echo "Error: Required model file not found: ../model/$file"
        exit 1
    fi
done

echo "✓ All required model files found"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed successfully"

# Start the API
echo "Starting RoBERTa Classifier API..."
echo "API will be available at: http://localhost:9000"
echo "Health check: http://localhost:9000/health"
echo "API documentation: http://localhost:9000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"

# Run the API
python main.py

