import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    response = requests.get("http://localhost:8000/health")
    print("\n=== Health Check ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_policy_comparison():
    url = f"{BASE_URL}/policy/compare"
    payload = {
        "policy1": "We will reduce carbon emissions by 50% by 2030 through renewable energy adoption.",
        "policy2": "Our goal is to cut greenhouse gas emissions in half by 2030 using solar and wind power."
    }
    response = requests.post(url, json=payload)
    print("\n=== Policy Comparison Test ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_weather_recommendation():
    url = f"{BASE_URL}/recommendations/"
    payload = {
        "location": "Colombo",
        "month": 8,
        "temperature_c": 29.5,
        "humidity_pct": 78,
        "wind_kmh": 10.0
    }
    response = requests.post(url, json=payload)
    print("\n=== Weather Recommendation Test ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    print("Starting API Tests...")
    try:
        test_health()
        test_policy_comparison()
        test_weather_recommendation()
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the server. Make sure the server is running on http://localhost:8000")