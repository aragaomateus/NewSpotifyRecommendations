import pandas as pd
import playlist_functions as pf
import numpy as np
import time 
# Read your existing data if the file exists, otherwise create an empty DataFrame
try:
    df_existing = pd.read_csv('artist_name_genres.csv')
except FileNotFoundError:
    df_existing = pd.DataFrame(columns=['name','id','genres'])
    df_existing.to_csv('artist_name_genres.csv', index=False)  # Create the file if it doesn't exist

# Convert the 'name' column to a list for quick membership checks
existing_names = df_existing['genres'].tolist()

# for g in existing_names:
#     if g is not np.nan:

#         print(g.split('-'))

# Load your artist IDs
data = pd.read_csv('../data/artist_avg_features.csv')
artist_ids = data.artist_id.to_list()
chunk_size = 50

artist_data = []  # Initialize an empty list to store artist dictionaries

for i in range(0,len(artist_ids), chunk_size):
    current_chunk = artist_ids[i:i+chunk_size]
    response = pf.api_request('/artists', params={'ids': ','.join(current_chunk)})
    
    for artist in response['artists']:
        if artist['name'] not in existing_names:
            # Append the dictionary to the artist_data list
            artist_data.append({
                'name': artist['name'],
                'id': artist['id'],
                'genres': '-'.join(artist['genres'])  # This will be a list
                
            })
    time.sleep(2)
# Convert the list of dictionaries to a DataFrame
df_artists = pd.DataFrame(artist_data)

# Append new data to the existing CSV if there is any new data
if not df_artists.empty:
    df_artists.to_csv('artist_name_genres.csv', mode='a', header=False, index=False)
