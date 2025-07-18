# roberta_classifier_api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import RobertaForSequenceClassification, RobertaTokenizer
import logging
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    filename='roberta_classifier_api.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    load_model()
    yield
    # Shutdown
    pass

app = FastAPI(title="RoBERTa Classifier API", version="1.0.0", lifespan=lifespan)

# Global variables for model and tokenizer
model = None
tokenizer = None

# Labels mapping (based on the config.json)
LABEL_MAPPING = {
    0: "LABEL_0",  # You can customize these labels based on your use case
    1: "LABEL_1",
    2: "LABEL_2", 
    3: "LABEL_3"
}

# Model path
MODEL_PATH = "../model"

class Input(BaseModel):
    response: str

class ClassificationResult(BaseModel):
    level: int
    label: str
    confidence: float
    probabilities: dict

def load_model():
    """Load the RoBERTa model and tokenizer"""
    global model, tokenizer
    
    try:
        logging.info(f"Loading model from {MODEL_PATH}")
        
        # Load tokenizer
        tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
        
        # Load model
        model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
        
        # Set model to evaluation mode
        model.eval()
        
        logging.info("Model and tokenizer loaded successfully")
        
    except Exception as e:
        logging.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {e}")

def classify_text(text: str):
    """Classify the input text using the RoBERTa model"""
    try:
        # Tokenize the input
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )
        
        # Make prediction
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # Get the predicted class and confidence
        predicted_class = torch.argmax(predictions, dim=-1).item()
        confidence = predictions[0][predicted_class].item()
        
        # Get all probabilities
        probabilities = {
            LABEL_MAPPING[i]: predictions[0][i].item() 
            for i in range(len(LABEL_MAPPING))
        }
        
        return {
            "level": predicted_class,
            "label": LABEL_MAPPING[predicted_class],
            "confidence": confidence,
            "probabilities": probabilities
        }
        
    except Exception as e:
        logging.error(f"Error during classification: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "RoBERTa Classifier API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model_loaded": True}

@app.post("/classify", response_model=ClassificationResult)
def classify(input: Input):
    """Classify the input text"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not input.response.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    
    logging.info(f"Classifying text: {input.response[:100]}...")  # Log first 100 chars
    
    result = classify_text(input.response)
    
    logging.info(f"Classification result: {result}")
    
    return result

@app.post("/classify_simple")
def classify_simple(input: Input):
    """Classify the input text (simple response format for backward compatibility)"""
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not input.response.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")
    
    logging.info(f"Classifying text: {input.response[:100]}...")  # Log first 100 chars
    
    result = classify_text(input.response)
    
    logging.info(f"Classification result: {result}")
    
    # Return simple format like the fake classifier
    return {"level": result["level"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)

