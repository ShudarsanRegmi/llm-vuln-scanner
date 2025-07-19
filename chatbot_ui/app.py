# chatbot_ui/app.py
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://localhost:8000/generate"

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    prompt = data.get("prompt", "")
    try:
        res = requests.post(API_URL, json={"prompt": prompt}, timeout=30)
        res.raise_for_status()
        response = res.json().get("response", "(No response)")
    except Exception as e:
        response = f"Error: {e}"
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(port=8502, debug=True)
