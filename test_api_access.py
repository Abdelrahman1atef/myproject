#!/usr/bin/env python3
"""
Script to test API access with token authentication
"""

import requests
import json

# Your API base URL
BASE_URL = "https://locust-eminent-urchin.ngrok-free.app/api"

# Your token
TOKEN = "089b79813f1cf73cf305fceae78710ce4cf60835"

# Headers for authentication
headers = {
    'Authorization': f'Token {TOKEN}',
    'Content-Type': 'application/json'
}

def test_api_endpoints():
    """Test various API endpoints"""
    
    endpoints = [
        '/admin/users/',
        '/admin/users/1/',  # Replace 1 with actual user ID
        '/products/see-our-products/',
        '/products/best-sellers/',
        '/product/allProducts/',
        '/me/',  # User profile
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n{'='*50}")
        print(f"Testing: {url}")
        print(f"{'='*50}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'results' in data:
                    print(f"Count: {data.get('count', 'N/A')}")
                    print(f"Results: {len(data.get('results', []))} items")
                    if data.get('results'):
                        print(f"First item keys: {list(data['results'][0].keys())}")
                else:
                    print(f"Response type: {type(data)}")
                    if isinstance(data, list):
                        print(f"Items: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

def test_specific_user():
    """Test getting a specific user's details"""
    user_id = 1  # Replace with actual user ID
    url = f"{BASE_URL}/admin/users/{user_id}/"
    
    print(f"\n{'='*50}")
    print(f"Testing User Details: {url}")
    print(f"{'='*50}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"User: {data.get('full_name', 'N/A')}")
            print(f"Email: {data.get('email', 'N/A')}")
            print(f"Total Orders: {data.get('total_orders', 'N/A')}")
            print(f"Total Spent: {data.get('total_spent', 'N/A')}")
            print(f"Order History: {len(data.get('order_history', []))} orders")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    print("Testing API Access with Token Authentication")
    print(f"Token: {TOKEN[:10]}...")
    
    test_api_endpoints()
    test_specific_user() 