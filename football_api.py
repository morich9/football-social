import requests

API_KEY = "a8896fbecf3b4d9ca2bb7bca0ae74cb4"
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