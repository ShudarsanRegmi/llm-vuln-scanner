# RoBERTa Classifier API

A FastAPI-based REST API for the RoBERTa text classifier model.

## Features

- **Real-time text classification** using a fine-tuned RoBERTa model
- **RESTful API** with FastAPI framework
- **Health check endpoints** for monitoring
- **Comprehensive logging** for debugging and monitoring
- **Multiple response formats** (detailed and simple)
- **Input validation** and error handling

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the model files are in the correct location:
   - The API expects the model files to be in `../model/` relative to the API directory
   - Required files: `config.json`, `model.safetensors`, `tokenizer_config.json`, `vocab.json`, `merges.txt`

## Usage

### Starting the API

```bash
# Run directly
python main.py

# Or with uvicorn
uvicorn main:app --reload --port 9000
```

The API will be available at `http://localhost:9000`

### API Endpoints

#### Health Check
- **GET** `/health` - Check if the model is loaded and API is ready
- **GET** `/` - Root endpoint with API information

#### Classification
- **POST** `/classify` - Detailed classification with confidence scores
- **POST** `/classify_simple` - Simple classification (backward compatible)

### Request Format

```json
{
  "response": "Your text to classify goes here"
}
```

### Response Formats

#### Detailed Response (`/classify`)
```json
{
  "level": 2,
  "label": "LABEL_2",
  "confidence": 0.85,
  "probabilities": {
    "LABEL_0": 0.05,
    "LABEL_1": 0.10,
    "LABEL_2": 0.85,
    "LABEL_3": 0.00
  }
}
```

#### Simple Response (`/classify_simple`)
```json
{
  "level": 2
}
```

## Example Usage

### Using curl

```bash
# Health check
curl -X GET http://localhost:9000/health

# Classification
curl -X POST http://localhost:9000/classify \
  -H "Content-Type: application/json" \
  -d '{"response": "This is a test message for classification"}'
```

### Using Python requests

```python
import requests

# Health check
response = requests.get('http://localhost:9000/health')
print(response.json())

# Classification
data = {"response": "This is a test message for classification"}
response = requests.post('http://localhost:9000/classify', json=data)
print(response.json())
```

## Model Information

- **Architecture**: RoBERTa for Sequence Classification
- **Classes**: 4 classes (LABEL_0, LABEL_1, LABEL_2, LABEL_3)
- **Max Input Length**: 512 tokens
- **Model Type**: Fine-tuned RoBERTa-base

## Logging

The API logs all requests and responses to `roberta_classifier_api.log` for monitoring and debugging.

## Error Handling

The API includes comprehensive error handling:
- Model loading errors (503 Service Unavailable)
- Empty input validation (400 Bad Request)
- Classification errors (500 Internal Server Error)

## Integration

This API is designed to replace the `fake_classifier_api` in the LLM vulnerability scanner system while maintaining the same interface for backward compatibility.

