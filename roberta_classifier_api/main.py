# roberta_classifier_api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import RobertaForSequenceClassification, RobertaTokenizer
import logging
import os
import random
from contextlib import asynccontextmanager

# Configure logging to console to avoid file permission issues
logging.basicConfig(
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
use_fallback = False  # Flag to indicate if we're using random fallback

# Labels mapping (based on the config.json)
LABEL_MAPPING = {
    0: "LABEL_0",  # You can customize these labels based on your use case
    1: "LABEL_1",
    2: "LABEL_2", 
    3: "LABEL_3"
}

# Model path
MODEL_PATH = "/home/aparichit/Projects/llm-vuln-scanner/roberta_response_classifier"

class Input(BaseModel):
    response: str

class ClassificationResult(BaseModel):
    level: int
    label: str
    confidence: float
    probabilities: dict

def load_model():
    """Load the RoBERTa model and tokenizer, or enable fallback mode"""
    global model, tokenizer, use_fallback
    
    try:
        logging.info(f"Attempting to load model from {MODEL_PATH}")
        
        # Load tokenizer
        tokenizer = RobertaTokenizer.from_pretrained(MODEL_PATH)
        
        # Load model
        model = RobertaForSequenceClassification.from_pretrained(MODEL_PATH)
        
        # Set model to evaluation mode
        model.eval()
        
        logging.info("RoBERTa model and tokenizer loaded successfully")
        use_fallback = False
        
    except Exception as e:
        logging.warning(f"Could not load RoBERTa model: {e}")
        logging.info("Enabling fallback mode - will return random classifications")
        model = None
        tokenizer = None
        use_fallback = True

def classify_text(text: str):
    """Classify the input text using RoBERTa model or fallback to random"""
    global use_fallback
    
    if use_fallback:
        # Fallback: return random classification between 0-3
        predicted_class = random.randint(0, 3)
        confidence = random.uniform(0.25, 0.95)  # Random confidence
        
        # Generate random probabilities that sum to 1
        raw_probs = [random.random() for _ in range(4)]
        total = sum(raw_probs)
        probabilities = {
            LABEL_MAPPING[i]: raw_probs[i] / total 
            for i in range(len(LABEL_MAPPING))
        }
        
        # Make sure the predicted class has the highest probability
        max_key = max(probabilities.keys(), key=lambda k: probabilities[k])
        if LABEL_MAPPING[predicted_class] != max_key:
            probabilities[LABEL_MAPPING[predicted_class]], probabilities[max_key] = probabilities[max_key], probabilities[LABEL_MAPPING[predicted_class]]
        
        logging.info(f"Using fallback classification: level {predicted_class}")
        
        return {
            "level": predicted_class,
            "label": LABEL_MAPPING[predicted_class],
            "confidence": confidence,
            "probabilities": probabilities
        }
    
    try:
        # Use actual RoBERTa model
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
        
        logging.info(f"RoBERTa classification: level {predicted_class}")
        
        return {
            "level": predicted_class,
            "label": LABEL_MAPPING[predicted_class],
            "confidence": confidence,
            "probabilities": probabilities
        }
        
    except Exception as e:
        logging.error(f"Error during RoBERTa classification: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "RoBERTa Classifier API is running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    if use_fallback:
        return {"status": "healthy", "model_loaded": False, "mode": "fallback"}
    elif model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model_loaded": True, "mode": "roberta"}

@app.post("/classify", response_model=ClassificationResult)
def classify(input: Input):
    """Classify the input text"""
    if not use_fallback and (model is None or tokenizer is None):
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
    if not use_fallback and (model is None or tokenizer is None):
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
    uvicorn.run(app, host="0.0.0.0", port=9000)

