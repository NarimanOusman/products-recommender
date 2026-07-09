import requests
import time

# URL of your running container API
URL = "http://127.0.0.1:8000/predict" 

# Payload matching the CustomerData schema from app.py
payload = {
    "total_events": 10.0,
    "unique_products": 5.0,
    "avg_price": 50.0,
    "max_price": 100.0,
    "purchase_count": 2.0,
    "view_count": 8.0,
    "cart_count": 1.0,
    "electronics_pref": 1.0,
    "unique_sessions": 3.0,
    "price_range": 2.0,
    "purchase_ratio": 0.2,
    "cart_ratio": 0.1,
    "view_ratio": 0.7,
    "avg_price_log": 3.9,
    "is_active_shopper": 1.0
}

def test_api_performance(n_requests):
    print(f"Sending {n_requests} requests to {URL}...")
    
    for i in range(n_requests):
        try:
            response = requests.post(URL, json=payload)
            if response.status_code == 200:
                print(f"Request {i+1}: Success - {response.json()['recommended_products']}")
            else:
                print(f"Request {i+1}: Failed - Status {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request {i+1}: Error - {e}")

if __name__ == "__main__":
    test_api_performance(10)