# fake_classifier_api/main.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
import random

app = FastAPI()

class Input(BaseModel):
    response: str

@app.post("/classify")
def classify(input: Input):
    fake_level = random.choice([0, 1, 2, 3])
    return {"level": fake_level}
