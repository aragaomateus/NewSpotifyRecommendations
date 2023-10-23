import json
import time
import playlist_functions as pf

# Constants
ARTIST_IDS_FILE = "artist_ids.txt"

def get_featured_playlists(limit=50, offset=0):
    """Get featured playlists."""
    endpoint = "/browse/featured-playlists"
    params = {
        'limit': limit,
        'offset': offset
    }
    print(f"[DEBUG] Fetching featured playlists with limit: {limit}, offset: {offset}")
    return pf.api_request(endpoint, params=params)

def get_tracks_from_playlist(playlist_id, limit=100, offset=0):
    """Get tracks from a specific playlist."""
    endpoint = f"/playlists/{playlist_id}/tracks"
    params = {
        'limit': limit,
        'offset': offset
    }
    print(f"[DEBUG] Fetching tracks from playlist with ID: {playlist_id}, limit: {limit}, offset: {offset}")
    return pf.api_request(endpoint, params=params)

import random

def get_available_genres():
    """Get available genres from Spotify."""
    endpoint = "/recommendations/available-genre-seeds"
    response = pf.api_request(endpoint)
    print(response)
    return response['genres']

def get_valid_categories():
    """Get valid categories from Spotify."""
    endpoint = "/browse/categories"
    response = pf.api_request(endpoint)
    categories = [category['id'] for category in response['categories']['items']]
    print(response)

    print('valid categories',categories)

    return categories

def get_playlists_by_genre(genre, limit=50):
    """Get playlists based on a specific genre."""
    endpoint = f"/browse/categories/{genre}/playlists"
    params = {'limit': limit}
    response = pf.api_request(endpoint, params=params)
    print(response['playlists']['items'])

    return response['playlists']['items']

def get_artist_ids_from_genre_playlists():
    all_artist_ids = set()
    genres = get_available_genres()
    valid_categories = get_valid_categories()  # Get valid categories

    # Only use genres that are valid categories
    # genres_to_process = set(genres) & set(valid_categories)

    # For each genre, fetch its playlists and extract artist IDs
    for idx, genre in enumerate(valid_categories):

        print(f"[DEBUG] Processing genre: {genre}")
        
        # Randomize starting offset
        offset = random.randint(0, 500)  # Adjust max value based on how deep you want to fetch
        
        try:
            playlists = get_playlists_by_genre(genre, limit=50)
        
            for playlist in playlists:
                playlist_id = playlist['id']
                tracks_data = get_tracks_from_playlist(playlist_id)
                
                for item in tracks_data['items']:
                    if item['track']:
                        for artist in item['track']['artists']:
                            all_artist_ids.add(artist['id'])
        except Exception as e:
            print(f"[ERROR] Failed to process genre '{genre}': {e}")
            continue
                        
        # Sleep to avoid rate limit 
        time.sleep(2)

    # Save artist IDs
    with open(ARTIST_IDS_FILE, "w") as file:
        for artist_id in all_artist_ids:
            file.write(f"{artist_id}\n")

    print(f"Saved {len(all_artist_ids)} artist IDs to {ARTIST_IDS_FILE}")

# Run the function
get_artist_ids_from_genre_playlists()
