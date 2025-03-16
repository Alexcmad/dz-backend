from faker import Faker
from datetime import datetime, timedelta
import random
import requests
import time

# Initialize Faker
fake = Faker()

# API base URL
BASE_URL = "http://127.0.0.1:8000"

# Predefined hazard types and their associated tags
HAZARD_TYPES = {
    'flooding': {
        'descriptions': [
            "Flooding reported at {location}",
            "Rising water levels at {location}",
            "Street flooding near {location}",
            "Flash flood warning at {location}",
            "Water accumulation at {location}"
        ],
        'tags': ['flood', 'water', 'infrastructure', 'emergency', 'weather']
    },
    'fire': {
        'descriptions': [
            "Fire outbreak at {location}",
            "Smoke visible from {location}",
            "Building fire reported at {location}",
            "Fire emergency at {location}",
            "Active fire situation at {location}"
        ],
        'tags': ['fire', 'emergency', 'smoke', 'evacuation', 'hazard']
    },
    'chemical': {
        'descriptions': [
            "Chemical spill at {location}",
            "Hazardous material leak near {location}",
            "Chemical odor reported at {location}",
            "Industrial chemical incident at {location}",
            "Chemical contamination at {location}"
        ],
        'tags': ['chemical', 'hazmat', 'industrial', 'emergency', 'contamination']
    },
    'traffic': {
        'descriptions': [
            "Major traffic incident at {location}",
            "Road blockage reported at {location}",
            "Traffic accident at {location}",
            "Vehicle collision at {location}",
            "Traffic congestion at {location}"
        ],
        'tags': ['traffic', 'road', 'accident', 'transportation', 'emergency']
    }
}

# Geographic boundaries (New York City area)
LAT_MIN, LAT_MAX = 40.4957, 40.9157  # NYC latitude range
LON_MIN, LON_MAX = -74.2557, -73.7002  # NYC longitude range

def create_test_users(num_users: int = 5):
    """Create test users through API"""
    users = []
    for i in range(num_users):
        user_data = {
            "email": fake.email(),
            "username": fake.user_name(),
            "password": "testpass123"  # Simple password for testing
        }
        
        try:
            response = requests.post(f"{BASE_URL}/users/", json=user_data)
            if response.status_code == 200:
                users.append(response.json())
                print(f"Created user: {user_data['username']}")
        except Exception as e:
            print(f"Error creating user: {e}")
    
    return users

def get_access_token(username: str, password: str):
    """Get access token for authentication"""
    try:
        response = requests.post(
            f"{BASE_URL}/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception as e:
        print(f"Error getting token: {e}")
    return None

def create_test_locations(access_token: str, num_locations: int = 20):
    """Create test locations through API"""
    locations = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    for _ in range(num_locations):
        location_data = {
            "name": fake.street_address(),
            "latitude": random.uniform(LAT_MIN, LAT_MAX),
            "longitude": random.uniform(LON_MIN, LON_MAX),
            "alert_level": random.randint(1, 5)
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/locations/",
                json=location_data,
                headers=headers
            )
            if response.status_code == 200:
                locations.append(response.json())
                print(f"Created location: {location_data['name']}")
        except Exception as e:
            print(f"Error creating location: {e}")
    
    return locations

def create_test_reports(access_token: str, locations: list, num_reports: int = 50):
    """Create test reports through API"""
    reports = []
    headers = {"Authorization": f"Bearer {access_token}"}
    
    for _ in range(num_reports):
        # Random location
        location = random.choice(locations)
        
        # Random hazard type and its details
        hazard_type = random.choice(list(HAZARD_TYPES.keys()))
        hazard_data = HAZARD_TYPES[hazard_type]
        
        # Generate content and tags
        content = random.choice(hazard_data['descriptions']).format(location=location['name'])
        tags = random.sample(hazard_data['tags'], random.randint(2, 4))
        
        report_data = {
            "content": content,
            "tags": tags,
            "location_id": location['id']
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/reports/",
                json=report_data,
                headers=headers
            )
            if response.status_code == 200:
                reports.append(response.json())
                print(f"Created report: {content[:50]}...")
                # Add a small delay to simulate real-world reporting
                time.sleep(0.5)
        except Exception as e:
            print(f"Error creating report: {e}")
    
    return reports

def main():
    # Create test users
    print("\nCreating test users...")
    users = create_test_users()
    if not users:
        print("No users created. Exiting.")
        return

    # Get access token for the first user
    access_token = get_access_token(users[0]['username'], "testpass123")
    if not access_token:
        print("Could not get access token. Exiting.")
        return

    # Create test locations
    print("\nCreating test locations...")
    locations = create_test_locations(access_token)
    if not locations:
        print("No locations created. Exiting.")
        return

    # Create test reports
    print("\nCreating test reports...")
    reports = create_test_reports(access_token, locations)

    # Print summary
    print("\nTest Data Generation Summary:")
    print(f"Created {len(users)} users")
    print(f"Created {len(locations)} locations")
    print(f"Created {len(reports)} reports")

    # Check events created by correlation
    try:
        response = requests.get(
            f"{BASE_URL}/events/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code == 200:
            events = response.json()
            print(f"System created {len(events)} correlated events")
    except Exception as e:
        print(f"Error checking events: {e}")

if __name__ == "__main__":
    main() 