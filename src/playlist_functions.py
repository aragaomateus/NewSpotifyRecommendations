import requests
import pandas as pd
import numpy as np
import time
import json
import os
import random
from scipy.spatial.distance import cosine
from dotenv import load_dotenv
import refresh_token as rt
# Load environment variables
load_dotenv()

# Constants
ARTIST_IDS_FILE = "../data/artist_ids.txt"
USED_ARTIST_IDS_FILE = "../data/used_artist_ids.txt"
BASE_URL = "https://api.spotify.com/v1"


# Global access token. Initialized with the token from environment variables.
ACCESS_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")


def api_request(endpoint, method="GET", data=None, params=None, access_token=None):
    """
    Makes an authenticated request to the Spotify API.

    Parameters:
    - endpoint: The API endpoint (excluding the base URL).
    - method: The HTTP method (GET, POST, etc.).
    - params: Any query parameters for the request.
    - access_token: The OAuth access token.

    Returns:
    - JSON response from the Spotify API.
    """
    if access_token is None:
        access_token = ACCESS_TOKEN

    headers = {
        'Authorization': f"Bearer {access_token}"
    }
    
    # print(f"Using headers: {headers}")
    response = requests.request(method, BASE_URL + endpoint, headers=headers, params=params, data=data)
    
    # Check for Unauthorized error
    if response.status_code == 401 or response.status_code == 400 :
        print("Token expired. Refreshing token and retrying.")
        access_token = rt.refresh_access_token()
        # print(f"Refreshed token after expiry: {access_token}")
        print('NEW TOKEN ISSUED')
        headers['Authorization'] = f"Bearer {access_token}"
        response = requests.request(method, BASE_URL + endpoint, headers=headers, params=params, data=data)

        if response.status_code == 401:
            raise ValueError("Failed to refresh access token. Please check your refresh token and credentials.")
    
    # If the request is successful
    if response.status_code == 200 or response.status_code == 201 :
        return response.json()
    # Handle rate limiting
    elif response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 1))
        print(f"Rate limit exceeded. Retrying in {retry_after} seconds.")
        time.sleep(retry_after)
        return api_request(endpoint, method,data, params, access_token)
    # For other HTTP errors
    else:
        print('its in the else',response.status_code)
        print(response.text)
        response.raise_for_status()

def fetch_spotify_generated_playlists(username, access_token=ACCESS_TOKEN):
    """
    Fetches Spotify's generated playlists (e.g., "Discover Weekly", "Daily Mix") for a specified user.

    Parameters:
    - username (str): Spotify username for which to fetch the generated playlists.
    - access_token (str, optional): Spotify access token. If not provided, will default to the global ACCESS_TOKEN.

    Returns:
    - pd.DataFrame: DataFrame containing details of the fetched playlists.
    """
    if access_token is None:
        access_token = ACCESS_TOKEN

    offset = 0
    limit = 50  # Maximum allowed by Spotify

    # List of Spotify generated playlists to search for
    generated_playlists = ["Discover Weekly", "Daily Mix 1", "Daily Mix 2", "Daily Mix 3", "Daily Mix 4", "Daily Mix 5", "Daily Mix 6"]

    playlist_details = []  # Will store details for each matched playlist

    while True:
        endpoint = f"/users/{username}/playlists"
        params = {
            'limit': limit,
            'offset': offset
        }
        
        playlists_data = api_request(endpoint, params=params, access_token=access_token)

        # Exit loop if no items are returned
        if not playlists_data['items']:
            break
        # Extract relevant details for playlists that match our criteria
        matching_playlists = [
            {
                'name': playlist['name'],
                'uri': playlist['uri'],
                'description': playlist.get('description', None),  # Handle case where 'description' might be absent
                'owner': playlist['owner']['display_name'],
                'image_url': playlist['images'][0]['url'] if playlist['images'] else None  # Take the highest resolution image, if available
            }

            for playlist in playlists_data['items']
            if any(name in playlist['name'] for name in generated_playlists)
        ]
        
        playlist_details.extend(matching_playlists)

        offset += limit

    # Convert the extracted playlist details into a DataFrame and return
    return pd.DataFrame(playlist_details)

def get_audio_features_for_tracks(track_ids, max_retries=5, delay_time=0.5):
    """
    Fetches audio features for a list of Spotify track IDs.

    Parameters:
    - track_ids (list of str): List of Spotify track IDs.
    - max_retries (int, optional): Maximum number of retries if an API request fails. Defaults to 5.
    - delay_time (float, optional): Time (in seconds) to wait between successive API requests. Defaults to 0.5.

    Returns:
    - list: List of audio features for the provided track IDs.
    """
    
    chunk_size = 50  # Spotify API allows up to 50 IDs in a single request
    collected_features = []
    
    for i in range(0, len(track_ids), chunk_size):
        current_chunk = track_ids[i:i+chunk_size]
        
        retries = 0
        while retries < max_retries:
            try:
                chunk_features_response = api_request('/audio-features', params={'ids': ','.join(current_chunk)})
                chunk_features = chunk_features_response.get('audio_features', [])
            except requests.exceptions.RequestException as e:
                response = e.response
                if response.status_code == 429:  # Too Many Requests
                    wait_time = int(response.headers.get('Retry-After', 1))
                    print(f"Rate limited! Waiting for {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    raise
                retries += 1
            else:
                if chunk_features:
                    collected_features.extend(chunk_features)
                break

        # If we reached max retries and haven't broken out of the loop
        if retries == max_retries:
            print(f"Max retries reached for chunk starting at index {i}. Some features might be missing.")
        
        # Delay between each request
        time.sleep(delay_time)
            
    return collected_features

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

def fetch_audio_features_for_playlist(playlist_row):
    """
    Fetch audio features for tracks in the given playlist row.

    Parameters:
    - playlist_row: Series containing playlist details with a 'uri' column pointing to the tracks of the playlist.

    Returns:
    - DataFrame containing audio features for the playlist.
    """

    # Extracting the playlist ID from the full URI
    playlist_id = playlist_row['uri'].split(':')[-1]
    
    # Constructing the endpoint to fetch tracks from the playlist
    tracks_endpoint = f"/playlists/{playlist_id}/tracks"

    tracks_data = api_request(tracks_endpoint)

    if not tracks_data or 'items' not in tracks_data:
        print(f"Couldn't fetch tracks for playlist ID: {playlist_id}. Skipping.")
        return pd.DataFrame()

    track_ids = [item['track']['id'] for item in tracks_data['items']]
    features_list = get_audio_features_for_tracks(track_ids)
        
    df = pd.DataFrame(features_list)

    return df

def get_hyper_playlist_recommendations(df, limit=10):
    """
    Fetches track recommendations based on the centroid of a playlist's audio features.
    
    Parameters:
    - df (DataFrame): DataFrame containing Spotify audio features for a playlist.
    - limit (int, optional): Maximum number of tracks to return. Defaults to 10.
    
    Returns:
    - DataFrame: A DataFrame containing the recommended tracks with their names, artists, popularity, and URIs.
    """
    
    features_of_interest = ["id", "danceability", "energy", "key", "loudness", "mode",
                            "speechiness", "acousticness", "instrumentalness",
                            "liveness", "valence", "tempo"]
    
    playlist_data = df[features_of_interest].copy()

    # Calculate centroid of the playlist features
    centroid = playlist_data[features_of_interest[1:]].mean()

    # Calculate distance of each track from the centroid
    playlist_data['distance'] = np.linalg.norm(playlist_data[features_of_interest[1:]].values - centroid.values, axis=1)

    # Get track data closest to the centroid
    center_track = playlist_data.nsmallest(1, 'distance').iloc[0]

    # Fetch detailed track and artist data
    track_data = api_request(f"/tracks/{center_track['id']}")
    artist_data = api_request(f"/artists/{track_data['artists'][0]['id']}")

    # Fetch track recommendations
    recommendations_params = {
        'seed_artists': artist_data['uri'].split(':')[2],
        'limit': limit
    }

    # Populate recommendation parameters with target features
    for feature in features_of_interest[1:]:
        recommendations_params[f'target_{feature}'] = center_track[feature]

    recommendations = api_request("/recommendations", params=recommendations_params)

    # Extract relevant information from the recommendations
    playlist_recommendations = [
        {
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "popularity": track['popularity'],
            "uri": track['uri']
        }
        for track in recommendations['tracks']
    ]

    return pd.DataFrame(playlist_recommendations)

def fetch_user_playlists(username, access_token= ACCESS_TOKEN):
    """
    Fetches all playlists created by a specific user on Spotify.
    
    Parameters:
    - username (str): Spotify username of the user whose playlists are to be fetched.
    - access_token (str): OAuth token to authenticate and authorize the Spotify API request.
    
    Returns:
    - DataFrame: A DataFrame containing details of each playlist such as name, URI, description, image URL, 
                public status, total number of tracks, username, and owner ID.
    """
    
    offset = 0
    limit = 50  # Maximum number of playlists that can be retrieved in one request by Spotify API

    playlists = []  # List to store details of each playlist as a dictionary

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
            playlists.append({
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
    playlists = pd.DataFrame(playlists)
    playlists = playlists[playlists['owner']== username]

    return playlists


def create_playlist(username, origin, recommendations):
    # Define your playlist details:
    playlist_name = f"{origin} Opposite playlits"
    playlist_description = "Generated based on opposite playlist recommendations."
    public_setting = True

    data = {
        "name": playlist_name,
        "description": playlist_description,
        "public": public_setting
    }

    endpoint = f"/users/{username}/playlists"
    playlist_info = api_request(endpoint, method="POST", data=json.dumps(data))
    print(playlist_info)
    try:
        print(f"Playlist ID: {playlist_info['id']}")
        print("Playlist created successfully!")
        
    except:
        print("Error in creating playlist.")
        print(playlist_info)

    # Endpoint to add tracks to the created playlist:
    add_tracks_endpoint = f"/playlists/{playlist_info['id']}/tracks"

    # Prepare the data:
    data = {
        "uris": list(recommendations['uri'])
    }

    response = api_request(add_tracks_endpoint, method="POST", data=json.dumps(data))

    if 'snapshot_id' in response:
        print("Tracks added successfully!")
    else:
        print("Error in adding tracks.")
        print(response)

def get_tracks_by_artist(artist_id):
    """
    Fetches top tracks for a given artist.

    Parameters:
    - artist_id (str): Spotify ID of the artist.

    Returns:
    - List[Dict]: List of top tracks for the given artist.
    """
    endpoint = f"/artists/{artist_id}/top-tracks"
    params = {'country': 'US'}  # Defaulting to US as the market
    return api_request(endpoint, params=params)['tracks']

def get_audio_features(track_id):
    """
    Fetches audio features for a given track.

    Parameters:
    - track_id (str): Spotify ID of the track.

    Returns:
    - Dict: Audio features of the given track.
    """
    endpoint = f"/audio-features/{track_id}"
    return api_request(endpoint)

def get_artist_ids_from_file(filename):
    """
    Reads artist IDs from a file.

    Parameters:
    - filename (str): Path to the file containing artist IDs.

    Returns:
    - List[str]: List of artist IDs.
    """
    with open(filename, 'r') as f:
        return [line.strip() for line in f.readlines()]

def save_used_artist_ids(artist_id, USED_ARTIST_IDS_FILE):
    """
    Appends an artist ID to a file.

    Parameters:
    - artist_id (str): The Spotify ID of the artist to save.
    - USED_ARTIST_IDS_FILE (str): Path to the file where the artist ID should be saved.
    """
    with open(USED_ARTIST_IDS_FILE, 'a') as f:
        f.write(f"{artist_id}\n")

def get_avg_features_for_artist(artist_id):
    """
    Fetches and calculates the average audio features for an artist's top tracks.

    Parameters:
    - artist_id (str): Spotify ID of the artist.

    Returns:
    - Dict: Average audio features for the artist's top tracks.
    """
    tracks = get_tracks_by_artist(artist_id)
    track_ids = [track['id'] for track in tracks]
    
    features_list = []
    for i in range(0, len(track_ids), 100):  # Batch request for tracks' features
        batch_track_ids = track_ids[i:i+100]
        features_batch = get_audio_features_for_tracks(batch_track_ids)
        features_list.extend(features_batch)
        time.sleep(0.5)  # To avoid hitting rate limits

    df = pd.DataFrame(features_list)
    for column in df.columns:  # Ensure columns are numeric
        df[column] = pd.to_numeric(df[column], errors='coerce')
    
    return df.mean().to_dict()

def get_audio_features_for_tracks(track_ids):
    """
    Fetches audio features for a batch of tracks.

    Parameters:
    - track_ids (List[str]): List of Spotify track IDs.

    Returns:
    - List[Dict]: List containing audio features for each track.
    """
    endpoint = f"/audio-features"
    params = {'ids': ','.join(track_ids)}
    return api_request(endpoint, params=params).get('audio_features', [])

def load_single_artist(artist_id, USED_ARTIST_IDS_FILE='../data/used_artist_ids.txt'):
    """
    Fetches average audio features for a single artist, saves the artist ID, 
    and appends the data to a CSV file.

    Parameters:
    - artist_id (str): Spotify ID of the artist.
    - USED_ARTIST_IDS_FILE (str, optional): Path to the file where used artist IDs are saved. Defaults to 'used_artist_ids.txt'.
    """
    avg_features_data = []

    try:
        print(f"[DEBUG] Processing artist ID: {artist_id}")
        avg_features = get_avg_features_for_artist(artist_id)
        avg_features['artist_id'] = artist_id
        avg_features_data.append(avg_features)
        
        save_used_artist_ids(artist_id, USED_ARTIST_IDS_FILE)
        temp_df = pd.DataFrame(avg_features_data)
        temp_df.to_csv('../data/artist_avg_features.csv', mode='a', header=not os.path.exists('../data/artist_avg_features.csv'), index=False)
        avg_features_data.clear()
        time.sleep(2)
    except Exception as e:
        print(f"[ERROR] Failed to process artist {artist_id}: {e}")

from scipy.spatial.distance import cosine

def find_opposite(artist_ids, df, n=10):
    """
    Find n artists that are most opposite in audio features to the given artist.
    
    Args:
    - artist_ids (list): List of artist ids.
    - df (DataFrame): Dataframe with average audio features.
    - n (int): Number of opposite artists to return.
    
    Returns:
    - list: A list of n artists that are most opposite to the given artist.
    """
    
    # Ensure 'artist_id' is the index, but only set it once
    if df.index.name != 'artist_id':
        df.set_index('artist_id', inplace=True)

    all_opposites = []

    for artist_id in artist_ids:
        if artist_id not in df.index:
            print(f"Artist '{artist_id}' not found in dataframe.")
            load_single_artist(artist_id,)  # Uncomment if this function exists and is required
            continue

        # Get the features of the specified artist
        artist_features = df.loc[artist_id]

        # Scale features
        scaled_df = (df - df.min()) / (df.max() - df.min())
        scaled_features = (artist_features - df.min()) / (df.max() - df.min())

        # Compute cosine distances
        def calculate_distance(x):
            try:
                return cosine(x.values, scaled_features.values)
            except:
                return float('inf')  # Assigning a large value for invalid rows; they won't be chosen as most opposite

        distances = scaled_df.apply(calculate_distance, axis=1)

        # Get the top n artists with the highest cosine distance (i.e., most opposite)
        opposites = distances.nsmallest(n).index.tolist()
        all_opposites.append(set(opposites))

    try: 
        intersection_of_opposites = set.intersection(*all_opposites)
        return list(intersection_of_opposites)
    except: 
        raise TypeError('No opposites found for intersection')


def get_opposite_playlist_recommendations(df, limit=15):
    """
    Provides recommendations for tracks that are opposite of the characteristics of the given playlist.

    Parameters:
    - df (pd.DataFrame): DataFrame containing track features.
    - limit (int, optional): Number of recommendations to fetch. Defaults to 15.

    Returns:
    - pd.DataFrame: DataFrame containing recommended tracks.
    """
    features_of_interest = ["id", "danceability", "energy", "key", "loudness", "mode",
                            "speechiness", "acousticness", "instrumentalness",
                            "liveness", "valence", "tempo"]

    playlist_data = df[features_of_interest].copy()

    # Calculate centroid of the playlist features
    centroid = playlist_data[features_of_interest[1:]].mean()

    # Find the distance of each track from the centroid
    playlist_data['distance'] = np.linalg.norm(playlist_data[features_of_interest[1:]].values - centroid.values, axis=1)

    # Get the track data closest to the centroid
    sorted_data = playlist_data.sort_values(by='distance')
    center = playlist_data[playlist_data['distance'] == playlist_data['distance'].min()]

    # Select the top 3 rows
    closest_tracks = sorted_data.head(3)
    artist_ids = []

    for idx,track in closest_tracks.iterrows():
        # Fetch track data
        track_data_response = api_request(f"/tracks/{track['id']}")
        track_data = track_data_response

        # Fetch artist data
        artist_ids.append(track_data['artists'][0]['id'])
        # artist_data_response = api_request(f"/artists/{artist_id}")
        print(track_data['artists'][0]['name'])
              
    print(artist_ids)
    artist_df = pd.read_csv('../data/artist_avg_features.csv', on_bad_lines='skip')
    opposites_seeds = []

    try:
        # opposites_seeds = find_opposite(artist_id, artist_df, n=3)
        opposites_seeds = find_opposite(artist_ids, artist_df)

    except ValueError as e: 
        opposites_seeds = artist_ids
        print(e)
    print(opposites_seeds)
    recommendations_response = api_request("/recommendations", params={
        'seed_artists':opposites_seeds ,
        'target_danceability':1-  center['danceability'].iloc[0],
        'target_energy':1- center['energy'].iloc[0],
        'target_mode':  1 if center['mode'].iloc[0] == 0 else 0,
        'target_key': center['key'].iloc[0],
        'target_speechiness':1- center['speechiness'].iloc[0],
        'target_acousticness':1- center['acousticness'].iloc[0],
        'target_instrumentalness':1- center['instrumentalness'].iloc[0],
        'target_liveness':1- center['liveness'].iloc[0],
        'target_valence':1- center['valence'].iloc[0],
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


# def fetch_recent_tracks(username, access_token= ACCESS_TOKEN):
#     """
#     Fetches all playlists created by a specific user on Spotify.
    
#     Parameters:
#     - username (str): Spotify username of the user whose playlists are to be fetched.
#     - access_token (str): OAuth token to authenticate and authorize the Spotify API request.
    
#     Returns:
#     - DataFrame: A DataFrame containing details of each playlist such as name, URI, description, image URL, 
#                 public status, total number of tracks, username, and owner ID.
#     """
    
#     offset = 0
#     limit = 50  # Maximum number of playlists that can be retrieved in one request by Spotify API



#     endpoint = f"/users/{username}/player/recently-played"
#     params = {
#         'limit': limit,
#         'offset': offset
#     }
#     playlists_data = api_request(endpoint, params=params, access_token=access_token)
#     print(playlists_data)
#     # if not playlists_data['items']:
#     #     break

#     # for playlist in playlists_data['items']:
#     #     playlists.append({
#     #         'name': playlist['name'],
#     #         'uri': playlist['uri'],
#     #         'description': playlist.get('description', None),
#     #         'image_url': playlist['images'][0]['url'] if playlist['images'] else None,
#     #         'public': playlist['public'],
#     #         'total_tracks': playlist['tracks']['total'],
#     #         'username': username,
#     #         'owner': playlist['owner']['id']
#     #     })

#     offset += limit



# def create_hyper_playlist_from_top_playlists(playlists_df, limit=10):
#     """
#     Creates a hyper playlist based on the top playlists of a user.

#     Parameters:
#     - playlists_df: DataFrame containing user's playlists.
#     - limit: Number of tracks to consider for hyper playlist generation.

#     Returns:
#     - Top 3 user's playlists (DataFrame).
#     - Hyper playlist (DataFrame).
#     """
#     # 1. Sort the playlists based on track count
#     sorted_playlists = playlists_df.sort_values(by="total_tracks", ascending=False)

#     owner_playlist= sorted_playlists[sorted_playlists['owner'] == sorted_playlists['username'] ]
#     # 2. Select the top 3 playlists
#     top_3_playlists = owner_playlist.head(3)
    
#     all_track_ids = []
#     # 3. Sample a maximum of 60 tracks from these 3 playlists
#     for idx, row in top_3_playlists.iterrows():
#         playlist_id = row['uri'].split(':')[-1]
#         tracks_endpoint = f"/playlists/{playlist_id}/tracks"
#         tracks_data = api_request(tracks_endpoint)

#         # Ensure item['track'] is not None before extracting the id
#         track_ids = []
#         for item in tracks_data['items']:
#             if item['track']:
#                 track_ids.append(item['track']['id'])

#         all_track_ids.extend(track_ids)
    
#     # If we have more than 60 tracks, we need to sample
#     if len(all_track_ids) > 60:
#         all_track_ids = random.sample(all_track_ids, 60)
    
#     # 4. Use these tracks to calculate audio features
#     features_df = pd.DataFrame(get_audio_features_for_tracks(all_track_ids))
    
#     # Fetch hyper playlist of 20 songs based on these audio features
#     hyper_playlist = get_hyper_playlist_recommendations(features_df, limit).head(20)
    
#     return top_3_playlists,hyper_playlist
