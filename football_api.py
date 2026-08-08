import requests

import os
API_KEY = os.environ.get("FOOTBALL_API_KEY", "bac35b2d51dffe8aeeb0f320a2108542")
BASE_URL = "https://api.football-data.org/v4"

HEADERS = {"X-Auth-Token": API_KEY}

def get_live_matches():
    url = f"{BASE_URL}/matches"
    params = {"status": "LIVE"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()

def get_scheduled_matches():
    url = f"{BASE_URL}/matches"
    params = {"status": "SCHEDULED"}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.json()