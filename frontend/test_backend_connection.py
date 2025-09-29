#!/usr/bin/env python3
"""
Test backend connection and query functionality
"""

import requests
import json

def test_backend():
    """Test backend connection and query"""
    print("🔍 Testing Backend Connection...")
    
    # Test 1: Health check
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend health check: OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False
    
    # Test 2: Simple query without language parameter
    try:
        print("\n🔍 Testing simple query (without language parameter)...")
        payload = {"query": "test query"}
        response = requests.post(
            "http://localhost:8000/api/v1/query/process",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Simple query: SUCCESS")
            print(f"   Success: {result.get('success')}")
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Simple query failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Simple query error: {e}")
        return False
    
    # Test 3: Query with language parameter
    try:
        print("\n🔍 Testing query with language parameter...")
        payload = {"query": "test query", "language": "en"}
        response = requests.post(
            "http://localhost:8000/api/v1/query/process",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query with language: SUCCESS")
            print(f"   Success: {result.get('success')}")
            return True
        else:
            print(f"❌ Query with language failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Query with language error: {e}")
        return False

if __name__ == "__main__":
    test_backend()
