
import requests
import pandas as pd
import numpy as np
import time
import base64
import os
import random

import os
from dotenv import load_dotenv
import requests

load_dotenv()


BASE_URL = "https://api.spotify.com/v1"

import refresh_token as rt 

access_token = os.getenv("SPOTIFY_REFRESH_TOKEN")


def api_request(endpoint, method="GET", params=None, access_token=None):
    if not access_token:
        print("Initial access token not provided. Refreshing...")
        access_token = rt.refresh_access_token()
        print(f"Refreshed token: {access_token}")
        
    headers = {
        'Authorization': f"Bearer {access_token}"
    }
    print(f"Using headers: {headers}")
    response = requests.request(method, BASE_URL + endpoint, headers=headers, params=params)
    
    # Check for Unauthorized error
    if response.status_code == 401:
        print("Token expired. Refreshing token and retrying.")
        access_token = rt.refresh_access_token()
        print(f"Refreshed token after expiry: {access_token}")
        headers['Authorization'] = f"Bearer {access_token}"
        response = requests.request(method, BASE_URL + endpoint, headers=headers, params=params)

        if response.status_code == 401:
            raise ValueError("Failed to refresh access token. Please check your refresh token and credentials.")
    
    # If the request is successful
    if response.status_code == 200:
        return response.json()
    # Handle rate limiting
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Retrying in {retry_after} seconds.")
        time.sleep(retry_after)
        return api_request(endpoint, method, params, access_token)
    # For other HTTP errors
    else:
        print(response.text)
        response.raise_for_status()

def fetch_spotify_generated_playlists(username):
    offset = 0
    limit = 50  # Maximum allowed by Spotify
    generated_playlists = ["Discover Weekly", "Daily Mix 1", "Daily Mix 2", "Daily Mix 3", "Daily Mix 4", "Daily Mix 5", "Daily Mix 6"]

    rows = []  # We'll store each playlist's info as a dictionary in this list, and later convert it to a DataFrame

    while True:
        endpoint = f"/users/{username}/playlists"
        params = {
            'limit': limit,
            'offset': offset
        }
        playlists_data = api_request(endpoint, params=params, access_token=access_token)
        if not playlists_data['items']:
            break

        for playlist in playlists_data['items']:
            if any(name in playlist['name'] for name in generated_playlists):
                rows.append({
                    'name': playlist['name'],
                    'uri': playlist['uri'],
                    'description': playlist.get('description', None),  # Using .get() in case 'description' doesn't exist for some reason
                    'image_url': playlist['images'][0]['url'] if playlist['images'] else None  # Assuming the first image is the best quality. Some playlists might not have images, hence the check.
                })

        offset += limit

    # Convert the list of dictionaries to a DataFrame and return it
    df = pd.DataFrame(rows)
    return df

def get_audio_features_for_tracks(track_ids, max_retries=5, delay_time=0.5):
    chunk_size = 50  # Spotify API allows up to 50 IDs in a single request
    features_list = []
    
    for i in range(0, len(track_ids), chunk_size):
        current_chunk = track_ids[i:i+chunk_size]
        
        retries = 0
        while retries < max_retries:
            try:
                chunk_features_response = api_request('/audio-features', params={'ids': ','.join(current_chunk)})
                chunk_features = chunk_features_response.get('audio_features', [])
                if chunk_features:
                    features_list.extend(chunk_features)
                break
            except requests.exceptions.RequestException as e:
                response = e.response
                if response.status_code == 429:  # Too Many Requests
                    wait_time = int(response.headers.get('Retry-After', 1))
                    print(f"Rate limited! Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    raise
            retries += 1

        # Delay between each request
        time.sleep(delay_time)
            
    return features_list


def fetch_audio_features_for_playlists(playlists_df):
    """
    Fetch audio features for tracks in each playlist from the given dataframe.

    Parameters:
    - playlists_df: DataFrame containing playlists with a 'uri' column pointing to the tracks of the playlist.

    Returns:
    - List of DataFrames containing audio features for each playlist.
    """
    dataframes = []
    
    for idx, row in playlists_df.iterrows():
        # Extracting the playlist ID from the full URI
        playlist_id = row['uri'].split(':')[-1]
        # Constructing the endpoint to fetch tracks from the playlist
        tracks_endpoint = f"/playlists/{playlist_id}/tracks"

        tracks_data = api_request(tracks_endpoint)

        if not tracks_data or 'items' not in tracks_data:
            print(f"Couldn't fetch tracks for playlist ID: {playlist_id}. Skipping.")
            continue

        track_ids = [item['track']['id'] for item in tracks_data['items']]
        features_list = get_audio_features_for_tracks(track_ids)
        
        df = pd.DataFrame(features_list)
        dataframes.append(df)

    return dataframes


def get_hyper_playlist_recommendations(df,limit = 10):
    
    features_of_interest = ["id", "danceability", "energy", "key", "loudness", "mode",
                            "speechiness", "acousticness", "instrumentalness",
                            "liveness", "valence", "tempo"]

    playlist_data = df[features_of_interest].copy()

    # Calculate centroid of the playlist features
    centroid = playlist_data[features_of_interest[1:]].mean()

    # Find the distance of each track from the centroid
    playlist_data['distance'] = np.linalg.norm(playlist_data[features_of_interest[1:]].values - centroid.values, axis=1)

    # Get the track data closest to the centroid
    center = playlist_data[playlist_data['distance'] == playlist_data['distance'].min()]

    # Fetch track data
    track_data_response = api_request(f"/tracks/{center['id'].iloc[0]}")
    track_data = track_data_response

    # Fetch artist data
    artist_id = track_data['artists'][0]['id']
    artist_data_response = api_request(f"/artists/{artist_id}")
    artist_data = artist_data_response

    recommendations_response = api_request("/recommendations", params={
        'seed_artists': artist_data['uri'].split(':')[2],
        'target_danceability': center['danceability'].iloc[0],
        'target_energy': center['energy'].iloc[0],
        'target_mode': center['mode'].iloc[0],
        'target_key': center['key'].iloc[0],
        'target_speechiness': center['speechiness'].iloc[0],
        'target_acousticness': center['acousticness'].iloc[0],
        'target_instrumentalness': center['instrumentalness'].iloc[0],
        'target_liveness': center['liveness'].iloc[0],
        'target_valence': center['valence'].iloc[0],
        'limit': limit
    })
    
    recommendations = recommendations_response
    playlist_recommendations = []

    for track in recommendations['tracks']:
        playlist_recommendations.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "popularity": track['popularity'],
            "uri": track['uri']
        })

    return pd.DataFrame(playlist_recommendations)



def fetch_user_playlists(username):
    offset = 0
    limit = 50  # Maximum allowed by Spotify

    rows = []  # We'll store each playlist's info as a dictionary in this list, and later convert it to a DataFrame

    while True:
        endpoint = f"/users/{username}/playlists"
        params = {
            'limit': limit,
            'offset': offset
        }
        playlists_data = api_request(endpoint, params=params, access_token=access_token)
        if not playlists_data['items']:
            break

        for playlist in playlists_data['items']:
            # Unlike the previous function, no need to filter based on playlist name
            rows.append({
                'name': playlist['name'],
                'uri': playlist['uri'],
                'description': playlist.get('description', None),
                'image_url': playlist['images'][0]['url'] if playlist['images'] else None,
                'public': playlist['public'],
                'total_tracks': playlist['tracks']['total'],
                'username': username,
                'owner': playlist['owner']['id']
            })

        offset += limit

    # Convert the list of dictionaries to a DataFrame and return it
    df = pd.DataFrame(rows)
    return df


def create_hyper_playlist_from_top_playlists(playlists_df, limit):
    # 1. Sort the playlists based on track count
    sorted_playlists = playlists_df.sort_values(by="total_tracks", ascending=False)

    owner_playlist= sorted_playlists[sorted_playlists['owner'] == sorted_playlists['username'] ]
    # 2. Select the top 3 playlists
    top_3_playlists = owner_playlist.head(3)
    print(top_3_playlists)
    
    all_track_ids = []
    # 3. Sample a maximum of 60 tracks from these 3 playlists
    for idx, row in top_3_playlists.iterrows():
        playlist_id = row['uri'].split(':')[-1]
        tracks_endpoint = f"/playlists/{playlist_id}/tracks"
        tracks_data = api_request(tracks_endpoint)

        # Ensure item['track'] is not None before extracting the id
        track_ids = []
        for item in tracks_data['items']:
            if item['track']:
                track_ids.append(item['track']['id'])

        all_track_ids.extend(track_ids)
    
    # If we have more than 60 tracks, we need to sample
    if len(all_track_ids) > 60:
        all_track_ids = random.sample(all_track_ids, 60)
    
    # 4. Use these tracks to calculate audio features
    features_df = pd.DataFrame(get_audio_features_for_tracks(all_track_ids))
    
    # Fetch hyper playlist of 20 songs based on these audio features
    hyper_playlist = get_hyper_playlist_recommendations(features_df, limit).head(20)
    
    return hyper_playlist

def create_new_spotify_playlist(user_id, playlist_name, track_uris):
    """
    Create a new playlist in the user's Spotify account and add tracks to it.

    Parameters:
    - user_id: The Spotify user ID.
    - playlist_name: The name of the new playlist.
    - track_uris: A list of Spotify track URIs.
    - access_token: Spotify API access token.

    Returns:
    - The created playlist's data or None if an error occurred.
    """
    # Create a new playlist
    create_playlist_endpoint = f"/users/{user_id}/playlists"
    playlist_data = {
        'name': playlist_name,
        'description': 'Generated based on hyper playlist recommendations.',
        'public': False,
        'uris': track_uris
    }
    response = api_request(create_playlist_endpoint, method="POST", data=playlist_data, access_token=access_token)
    
    if 'id' not in response:
        print("Failed to create playlist.")
        return None

    playlist_id = response['id']

    # Add tracks to the created playlist
    add_tracks_endpoint = f"/playlists/{playlist_id}/tracks"
    tracks_data = {
        "uris": track_uris
    }

    response = api_request(add_tracks_endpoint, method="POST", params=tracks_data, access_token=access_token)

    if 'snapshot_id' not in response:
        print("Failed to add tracks to playlist.")
        return None

    return response
# Use the function like this:
jaden_username = '22yxmxhcofugil76dz26cbyri'

ange_user= "2232daj5rpzsst52fu4oaswwq"
leo_user = '31nqdjtmuec6hqotb4y6cohzdb5m'
fetched_playlists = fetch_user_playlists('aragaosm')
# print(fetched_playlists)
# for idx, item in fetched_playlists.iterrows():
#     print(item['name'],item['total_tracks'],item['owner'],item['public']) 
hyper_playlist = create_hyper_playlist_from_top_playlists(fetched_playlists,20)
for idx, item in hyper_playlist.iterrows(): 
    print(item['name'],'-',item['artist'])


# create_new_spotify_playlist('aragaosm', 'argaosm Recommendation by Mateus', hyper_playlist['uri'])

import requests
import json

BASE_URL = "https://api.spotify.com/v1/"
USER_ID = "aragaosm"
ACCESS_TOKEN = rt.refresh_access_token() # Make sure this token has the necessary scope for creating playlists

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# Define your playlist details:
playlist_name = f"{'aragaosm'} Recommendation by Mateus"
playlist_description = "Generated based on hyper playlist recommendations."
public_setting = True

data = {
    "name": playlist_name,
    "description": playlist_description,
    "public": public_setting
}

endpoint = f"users/{USER_ID}/playlists"
response = requests.post(BASE_URL + endpoint, headers=headers, data=json.dumps(data))

if response.status_code == 201:  # HTTP 201 Created
    print("Playlist created successfully!")
    playlist_info = response.json()
    print(f"Playlist ID: {playlist_info['id']}")
else:
    print("Error in creating playlist.")
    print(response.json())


# Endpoint to add tracks to the created playlist:
add_tracks_endpoint = f"playlists/{playlist_info['id']}/tracks"

# Prepare the data:
data = {
    "uris": list(hyper_playlist['uri'])
}

response = requests.post(BASE_URL + add_tracks_endpoint, headers=headers, data=json.dumps(data))

if response.status_code == 201:  # HTTP 201 Created
    print("Tracks added successfully!")
else:
    print("Error in adding tracks.")
    print(response.json())
    