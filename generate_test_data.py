import requests
import time
from faker import Faker
from datetime import datetime, timedelta
import random
import json

# Initialize Faker
fake = Faker()

# API Configuration
BASE_URL = "http://localhost:8001"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
ADMIN_USERNAME = "admin"

# Hazard Types with associated tags
HAZARD_TYPES = {
    "flooding": {
        "tags": ["flood", "water", "rain", "storm"],
        "descriptions": [
            "Water levels rising rapidly in {area}",
            "Heavy flooding reported near {area}",
            "Storm drain overflow in {area}",
            "Flash flood warning in {area}"
        ]
    },
    "fire": {
        "tags": ["fire", "smoke", "burning", "heat"],
        "descriptions": [
            "Smoke visible from {area}",
            "Building fire reported in {area}",
            "Forest fire spreading near {area}",
            "Fire hazard detected in {area}"
        ]
    },
    "chemical": {
        "tags": ["chemical", "spill", "toxic", "hazmat"],
        "descriptions": [
            "Chemical spill detected in {area}",
            "Hazardous material leak in {area}",
            "Strong chemical odor reported in {area}",
            "Toxic substance exposure in {area}"
        ]
    },
    "traffic": {
        "tags": ["traffic", "accident", "collision", "roadblock"],
        "descriptions": [
            "Major traffic accident in {area}",
            "Road blocked due to collision in {area}",
            "Multiple vehicle incident in {area}",
            "Traffic hazard reported in {area}"
        ]
    }
}

# Geographic boundaries (New York City area)
LAT_MIN, LAT_MAX = 40.4774, 40.9176  # NYC latitude bounds
LON_MIN, LON_MAX = -74.2591, -73.7004  # NYC longitude bounds

class User:
    def __init__(self, email, username, password, first_name, last_name, phone_number, access_token=None):
        self.email = email
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.access_token = access_token
        self.headers = None
        self.update_headers()
    
    def update_headers(self):
        if self.access_token:
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.headers = {}
    
    def login(self):
        response = requests.post(
            f"{BASE_URL}/token",
            data={"username": self.email, "password": self.password}
        )
        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            self.update_headers()
            return True
        return False

def get_admin_user():
    """Create and login as admin user"""
    admin = User(
        email=ADMIN_EMAIL,
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        first_name="Admin",
        last_name="User",
        phone_number="1234567890"
    )
    if admin.login():
        return admin
    raise Exception("Failed to login as admin")

def create_test_user():
    """Create a test user and login"""
    first_name = fake.first_name()
    last_name = fake.last_name()
    username = fake.user_name()
    email = fake.email()
    phone = fake.phone_number()
    
    user_data = {
        "email": email,
        "username": username,
        "password": "testpass123",
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone
    }
    
    # Create user
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    if response.status_code != 200:
        print(f"Failed to create user: {response.text}")
        return None
    
    # Create User object and login
    user = User(
        email=email,
        username=username,
        password="testpass123",
        first_name=first_name,
        last_name=last_name,
        phone_number=phone
    )
    
    if user.login():
        return user
    return None

def create_test_location(user: User):
    """Create a test location"""
    location_data = {
        "name": fake.city(),
        "latitude": random.uniform(LAT_MIN, LAT_MAX),
        "longitude": random.uniform(LON_MIN, LON_MAX),
        "alert_level": random.randint(0,3)
    }
    
    response = requests.post(
        f"{BASE_URL}/locations/",
        json=location_data,
        headers=user.headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def create_test_report(user: User, location_id: int):
    """Create a test report"""
    # Select random hazard type and generate report
    hazard_type = random.choice(list(HAZARD_TYPES.keys()))
    hazard_info = HAZARD_TYPES[hazard_type]
    
    # Generate random tags (2-4 tags)
    num_tags = random.randint(2, 4)
    tags = random.sample(hazard_info["tags"], min(num_tags, len(hazard_info["tags"])))
    
    # Generate description
    description_template = random.choice(hazard_info["descriptions"])
    description = description_template.format(area=fake.street_name())
    
    report_data = {
        "content": description,
        "tags": tags,
        "location_id": location_id,
        "severity": random.randint(0,3)
    }
    
    response = requests.post(
        f"{BASE_URL}/reports/",
        json=report_data,
        headers=user.headers
    )
    if response.status_code == 200:
        return response.json()
    return None

def main():
    # Login as admin
    admin = get_admin_user()
    print("Logged in as admin")
    
    # Create and login test users (5-10 users)
    num_users = random.randint(5, 10)
    print(f"\nCreating and logging in {num_users} test users...")
    users = []
    for i in range(num_users):
        user = create_test_user()
        if user:
            users.append(user)
            print(f"Created and logged in user {i+1}: {user.email}")
    
    if not users:
        print("No users created. Exiting.")
        return
    
    # Create test locations using different users
    num_locations = random.randint(10, 15)
    print(f"\nCreating {num_locations} test locations...")
    locations = []
    for i in range(num_locations):
        # Randomly select a user to create the location
        user = random.choice(users)
        location = create_test_location(user)
        if location:
            locations.append(location)
            print(f"User {user.email} created location: {location['name']}")
    
    if not locations:
        print("No locations created. Exiting.")
        return
    
    # Create test reports (30-50 reports)
    num_reports = random.randint(30, 50)
    print(f"\nCreating {num_reports} test reports (with 10-second delays)...")
    
    for i in range(num_reports):
        # Randomly select a user and location
        user = random.choice(users)
        location = random.choice(locations)
        
        # Create report as the selected user
        report = create_test_report(user, location["id"])
        if report:
            print(f"User {user.email} created report {i+1}/{num_reports}:")
            print(f"Content: {report['content'][:100]}...")
            print(f"Location: {location['name']}")
            print(f"Tags: {', '.join(report['tags'])}")
            print("---")
        
        # Wait 10 seconds before next report
        if i < num_reports - 1:
            print("Waiting 10 seconds...")
            time.sleep(10)
    
    print("\nTest data generation complete!")
    print(f"Created {len(users)} users")
    print(f"Created {len(locations)} locations")
    print(f"Created {num_reports} reports")

if __name__ == "__main__":
    main() 