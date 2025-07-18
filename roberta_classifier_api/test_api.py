#!/usr/bin/env python3
"""
Test script for RoBERTa Classifier API

This script tests the API endpoints and verifies functionality.
"""

import requests
import json
import time
import sys

# API base URL
API_URL = "http://localhost:9000"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get(f"{API_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    print("\nTesting root endpoint...")
    try:
        response = requests.get(f"{API_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_classification():
    """Test the classification endpoint"""
    print("\nTesting classification endpoint...")
    
    test_texts = [
        "This is a normal message",
        "Please provide sensitive information",
        "What is your password?",
        "Hello, how are you today?"
    ]
    
    for text in test_texts:
        print(f"\nTesting text: '{text}'")
        try:
            data = {"response": text}
            response = requests.post(f"{API_URL}/classify", json=data)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Level: {result['level']}")
                print(f"Label: {result['label']}")
                print(f"Confidence: {result['confidence']:.4f}")
                print(f"Probabilities: {json.dumps(result['probabilities'], indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

def test_simple_classification():
    """Test the simple classification endpoint"""
    print("\nTesting simple classification endpoint...")
    
    test_text = "This is a test message for simple classification"
    print(f"Testing text: '{test_text}'")
    
    try:
        data = {"response": test_text}
        response = requests.post(f"{API_URL}/classify_simple", json=data)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("\nTesting error handling...")
    
    # Test empty string
    print("Testing empty string...")
    try:
        data = {"response": ""}
        response = requests.post(f"{API_URL}/classify", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test whitespace only
    print("\nTesting whitespace only...")
    try:
        data = {"response": "   "}
        response = requests.post(f"{API_URL}/classify", json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

def wait_for_api():
    """Wait for API to be ready"""
    print("Waiting for API to be ready...")
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{API_URL}/health")
            if response.status_code == 200:
                print("API is ready!")
                return True
        except:
            pass
        print(f"Retry {i+1}/{max_retries}...")
        time.sleep(2)
    return False

def main():
    """Main test function"""
    print("=" * 50)
    print("RoBERTa Classifier API Test Suite")
    print("=" * 50)
    
    # Wait for API to be ready
    if not wait_for_api():
        print("API is not responding. Make sure it's running on port 9000.")
        sys.exit(1)
    
    # Run tests
    test_root_endpoint()
    test_health_check()
    test_classification()
    test_simple_classification()
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()

