import os
from dotenv import load_dotenv
import requests

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN") # This can be updated once you've obtained the initial refresh token.


import logging

logging.basicConfig(level=logging.INFO)  # configure logging

def refresh_access_token():
    CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
    CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")

    if not all([CLIENT_ID, CLIENT_SECRET, refresh_token]):
        logging.error("Required environment variables not set.")
        return None

    token_url = "https://accounts.spotify.com/api/token"
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    try:
        response = requests.post(token_url, data=refresh_data)
        response.raise_for_status()
        
        token_response_data = response.json()

        new_access_token = token_response_data.get('access_token')
        if not new_access_token:
            logging.error("Error: 'access_token' not found in the response.")
            logging.error(token_response_data)
            return None

        # If a new refresh token is provided (not always the case, but sometimes it happens)
        if 'refresh_token' in token_response_data:
            os.environ["SPOTIFY_REFRESH_TOKEN"] = token_response_data['refresh_token']

        return new_access_token

    except requests.RequestException as e:
        logging.error(f"HTTP Error during token refresh: {e}")
        return None
    except Exception as e:
        logging.error(f"Error during token refresh: {e}")
        return None

