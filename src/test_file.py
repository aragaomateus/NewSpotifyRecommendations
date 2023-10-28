import playlist_functions as pf
import refresh_token as rt
import requests
import json
import pandas as pd
# Use the function like this:
# jaden_username = '22yxmxhcofugil76dz26cbyri'

# ange_user= "2232daj5rpzsst52fu4oaswwq"
# leo_user = '31nqdjtmuec6hqotb4y6cohzdb5m'
# gui_user = '1255519925'
# fetched_playlists = pf.fetch_user_playlists(gui_user)
# # print(fetched_playlists)
# # for idx, item in fetched_playlists.iterrows():
# #     print(item['name'],item['total_tracks'],item['owner'],item['public']) 
# hyper_playlist = pf.create_hyper_playlist_from_top_playlists(fetched_playlists,20)
# for idx, item in hyper_playlist.iterrows(): 
#     print(item['name'],'-',item['artist'])


# # create_new_spotify_playlist('aragaosm', 'argaosm Recommendation by Mateus', hyper_playlist['uri'])
def create_playlist(username,origin, recommendations):
    BASE_URL = "https://api.spotify.com/v1/"
    ACCESS_TOKEN = rt.refresh_access_token() # Make sure this token has the necessary scope for creating playlists

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Define your playlist details:
    playlist_name = f"{origin} Opposite playlits"
    playlist_description = "Generated based on opposite playlist recommendations."
    public_setting = True

    data = {
        "name": playlist_name,
        "description": playlist_description,
        "public": public_setting
    }

    endpoint = f"users/{username}/playlists"
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
        "uris": list(recommendations['uri'])
    }

    response = requests.post(BASE_URL + add_tracks_endpoint, headers=headers, data=json.dumps(data))

    if response.status_code == 201:  # HTTP 201 Created
        print("Tracks added successfully!")
    else:
        print("Error in adding tracks.")
        print(response.json())
    

# --------------------------
playlists_df = pf.fetch_spotify_generated_playlists('aragaosm')
playlists_df =playlists_df[playlists_df['owner']== 'Spotify']
print(playlists_df)

# Fetch audio features for the entire playlist list
playlist_to_recommend = playlists_df.iloc[5]
audio_features_dfs = pf.fetch_audio_features_for_playlists(playlists_df)

recommendations = pf.get_opposite_playlist_recommendations(audio_features_dfs[5])
print(recommendations)

create_playlist('aragaosm',playlist_to_recommend['name'],recommendations)


#---------------------------
# df = pd.read_csv('../data/corrected_artist_avg_features.csv', on_bad_lines='skip')
# print(df)

# import pandas as pd

# # Define the expected number of columns
# expected_columns = 20

# # Initialize an empty DataFrame to store valid rows
# valid_df = pd.DataFrame()

# # Read the file line by line
# with open('../data/artist_avg_features.csv', 'r') as file:
#     # Skip the header row
#     header = next(file).strip().split(',')
    
#     for line in file:
#         # Split the line by comma
#         values = line.strip().split(',')
        
#         if len(values) == expected_columns:
#             # Convert the list of values to a DataFrame with a single row and append to valid_df
#             values = values[:len(values)-1]
#             row_df = pd.DataFrame([values], columns=header)
#             valid_df = pd.concat([valid_df, row_df], ignore_index=True)
#         else:
#             row_df = pd.DataFrame([values], columns=header)
#             valid_df = pd.concat([valid_df, row_df], ignore_index=True)

# # Save the valid rows back to a CSV
# valid_df.to_csv('../data/corrected_artist_avg_features.csv', index=False)


# with open('../data/artist_avg_features.csv','r') as file: 
#     for line in file:
#         if len(line.split(',')) == 20:
#             print(line.split(','))
#             print(line.split(',')[:len(line.split(','))-1])


# --------------------------------------


# playlists_df = pf.fetch_user_playlists('aragaosm')

# top_3,hyper_recommendations = pf.create_hyper_playlist_from_top_playlists(playlists_df)

# print(top_3,hyper_recommendations)

# import requests
# import json
