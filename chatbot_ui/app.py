# chatbot_ui/app.py
import streamlit as st
import requests

st.set_page_config(page_title="☕ BrewBot - Coffee Shop Chatbot")

st.title("☕ BrewBot - Coffee Shop Chatbot")

api_url = st.text_input("LLM API Endpoint", "http://localhost:8000/generate")
user_input = st.text_input("Ask BrewBot anything:")

if st.button("Send"):
    try:
        res = requests.post(api_url, json={"prompt": user_input})
        st.write("### BrewBot says:")
        st.success(res.json()["response"])
    except Exception as e:
        st.error(f"Error: {e}")
