"""Quick test script for check-in API endpoints.

Run this after starting the server with:
    uv run uvicorn app.main:app --reload
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint."""
    print("\n1. Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response.status_code == 200

def test_create_checkin():
    """Test creating a check-in."""
    print("\n2. Testing POST /api/v1/checkins...")
    
    checkin_data = {
        "venue_id": 1,
        "occupancy": 3,
        "noise": 2,
        "anonymous": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/checkins",
        json=checkin_data
    )
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   Created check-in ID: {data['id']}")
        print(f"   Venue: {data['venue_id']}")
        print(f"   Occupancy: {data['occupancy']}, Noise: {data['noise']}")
        print(f"   Time: {data['created_at']}")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_venue_stats():
    """Test getting venue statistics."""
    print("\n3. Testing GET /api/v1/venues/1/stats...")
    
    response = requests.get(f"{BASE_URL}/api/v1/venues/1/stats?minutes=5")
    
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Venue ID: {data['venue_id']}")
        print(f"   Avg Occupancy: {data['avg_occupancy']}")
        print(f"   Avg Noise: {data['avg_noise']}")
        print(f"   Check-in Count: {data['checkin_count']}")
        print(f"   Time Window: {data['time_window_minutes']} minutes")
        return True
    else:
        print(f"   Error: {response.text}")
        return False

def test_multiple_checkins():
    """Test creating multiple check-ins to verify aggregation."""
    print("\n4. Testing multiple check-ins for aggregation...")
    
    checkins = [
        {"venue_id": 1, "occupancy": 2, "noise": 1, "anonymous": True},
        {"venue_id": 1, "occupancy": 4, "noise": 3, "anonymous": True},
        {"venue_id": 1, "occupancy": 3, "noise": 2, "anonymous": True},
    ]
    
    for i, checkin in enumerate(checkins, 1):
        response = requests.post(f"{BASE_URL}/api/v1/checkins", json=checkin)
        if response.status_code == 201:
            print(f"   ✓ Check-in {i} created: occupancy={checkin['occupancy']}, noise={checkin['noise']}")
        else:
            print(f"   ✗ Check-in {i} failed: {response.text}")
            return False
    
    # Now check the stats
    print("\n   Getting updated stats...")
    response = requests.get(f"{BASE_URL}/api/v1/venues/1/stats?minutes=2")
    if response.status_code == 200:
        data = response.json()
        print(f"   Avg Occupancy: {data['avg_occupancy']:.2f} (should be ~3.0)")
        print(f"   Avg Noise: {data['avg_noise']:.2f} (should be ~2.0)")
        print(f"   Total Check-ins: {data['checkin_count']}")
        return True
    return False

def test_validation():
    """Test validation errors."""
    print("\n5. Testing validation...")
    
    # Invalid occupancy (>5)
    print("   a) Testing invalid occupancy (6)...")
    response = requests.post(
        f"{BASE_URL}/api/v1/checkins",
        json={"venue_id": 1, "occupancy": 6, "noise": 2}
    )
    if response.status_code == 422:
        print("   ✓ Correctly rejected invalid occupancy")
    else:
        print(f"   ✗ Should have rejected: {response.status_code}")
    
    # Invalid venue
    print("   b) Testing non-existent venue (999)...")
    response = requests.post(
        f"{BASE_URL}/api/v1/checkins",
        json={"venue_id": 999, "occupancy": 3, "noise": 2}
    )
    if response.status_code == 404:
        print("   ✓ Correctly rejected non-existent venue")
    else:
        print(f"   ✗ Should have returned 404: {response.status_code}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Check-In API Test Suite")
    print("=" * 60)
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    
    try:
        # Basic tests
        test_health()
        test_create_checkin()
        test_venue_stats()
        test_multiple_checkins()
        test_validation()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server")
        print("   Make sure the server is running:")
        print("   cd backend && uv run uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()

