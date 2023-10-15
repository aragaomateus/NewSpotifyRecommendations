import streamlit as st
import playlist_functions as pf
import pickle

def save_cache_to_file(cache, filename="cache.pkl"):
    """Saves the cache dictionary to a file."""
    with open(filename, "wb") as file:
        pickle.dump(cache, file)

def load_cache_from_file(filename="cache.pkl"):
    """Loads the cache dictionary from a file. If file doesn't exist, returns an empty dictionary."""
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return {}

from datetime import datetime, timedelta

# Your functions for generating the hyper and opposite playlists...

# Load the cache from file
CACHE = load_cache_from_file()

# Title and Description
st.title('Hyper & Opposite Playlist Generator')
st.write("Discover hyper-focused and polar opposite playlists based on your Spotify 'for you' playlist!")

# User input
username = st.text_input('Enter your Spotify username')

# Process and Display
if username.strip() != '':
    
    current_time = datetime.now()

    # Check if the data exists in the cache and if it's less than a day old
    if username in CACHE and (current_time - CACHE[username]['timestamp']) <= timedelta(days=1):
        playlists_df = CACHE[username]['playlists_df']
        audio_features_dfs = CACHE[username]['audio_features_dfs']
    else:
        # Fetch the user's playlists
        playlists_df = pf.fetch_spotify_generated_playlists(username)
        
        # Fetch audio features for the entire playlist list
        audio_features_dfs = pf.fetch_audio_features_for_playlists(playlists_df)

        CACHE[username] = {
            'timestamp': current_time,
            'playlists_df': playlists_df,
            'audio_features_dfs': audio_features_dfs
        }
        
        # Save the updated cache to file
        save_cache_to_file(CACHE)
    
    # Display each playlist with its image and hyper playlist suggestions
    for idx, (row, audio_features_df) in enumerate(zip(playlists_df.iterrows(), audio_features_dfs)):
        
        col1, col2 = st.columns(2)
        
        with col1:
            col1.write(row[1]['name'])
            col1.image(row[1]['image_url'], width=300)  # Set the width here
        
        with col2:
            # Fetch hyper playlist recommendations based on the current playlist audio features
            hyper_recommendations = pf.get_hyper_playlist_recommendations(audio_features_df)
            
            col2.write("Hyper Playlist Suggestions:")
            col2.write(hyper_recommendations)