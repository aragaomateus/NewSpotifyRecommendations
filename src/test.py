import playlist_functions as pf
import refresh_token as rt
import requests
import json
import pandas as pd
import numpy as np
import time
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import lyricsgenius

genius = lyricsgenius.Genius("lIV-gRX8KKDIZrT76bAnR3DGmDY8No2PyL_5TnrwMV03qSCHHm_guqR3YrVPHJPM")
genius.timeout = 10  # set timeout to 10 seconds

# song = genius.search_artist("The Notorious B.I.G.",max_songs=2)  # Replace with your desired song and artist
def fetch_artist_songs(artist_name, max_songs=10, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            return genius.search_artist(artist_name, max_songs=max_songs)
        except (requests.exceptions.Timeout, lyricsgenius.api.base.Timeout):
            retries += 1
            print(f"Timeout error. Retrying... {retries}/{max_retries}")
            time.sleep(5)  # Wait for 5 seconds before retrying
    print("Failed to fetch data after maximum retries.")
    return None

import os

def save_lyrics_to_csv(artist_list, max_songs=10, csv_filename="artists_lyrics.csv"):
    # Check if the file exists, if it does, read it
    if os.path.exists(csv_filename):
        df_existing = pd.read_csv(csv_filename)
    else:
        df_existing = pd.DataFrame(columns=["Artist", "Title_Lyrics"])

    all_data = {
        "Artist": [],
        "Title_Lyrics": []
    }

    for artist_name in artist_list:
        # If artist not in the existing dataframe, fetch their songs
        if artist_name not in df_existing["Artist"].unique():
            artist = fetch_artist_songs(artist_name, max_songs)
            if artist:
                for song in artist.songs:
                    all_data["Artist"].append(artist_name)
                    all_data["Title_Lyrics"].append(song.title + '\n' + song.lyrics)

    # Convert the gathered data into a dataframe
    df_new = pd.DataFrame(all_data)
    
    # Concatenate the new data with existing data and drop potential duplicates
    df_combined = pd.concat([df_existing, df_new]).drop_duplicates().reset_index(drop=True)
    
    # Save the combined data back to the CSV
    df_combined.to_csv(csv_filename, index=False)
    print(f"Lyrics saved to {csv_filename}")


def get_artist_vector(artist, df, vectorizer, max_songs=10):

    df_artist = df[df['Artist'] ==artist]

    # Combine all lyrics into one text
    combined_lyrics = combined_lyrics = ' '.join([ lyric for lyric in df_artist.Title_Lyrics])

    # Tokenizing into standardized size chunks, e.g., 100 words each
    tokens = combined_lyrics.split()
    chunks = [' '.join(tokens[i:i+100]) for i in range(0, len(tokens), 100)]

    # Transform the chunks using the already fitted vectorizer
    tfidf_matrix = vectorizer.transform(chunks)

    # Averaging the vectors
    average_vector = np.mean(tfidf_matrix, axis=0).A1

    return average_vector


artist_list = [
        "Kendrick Lamar", "The Notorious B.I.G.", "Barbra Streisand", "Taylor Swift", 
    "Bob Dylan", "Nina Simone", "Ludwig van Beethoven", "Shakira", 
    "Billie Eilish", "Ravi Shankar", "Daft Punk", "Hank Williams",
    "B.B. King", "The Chemical Brothers", "Amália Rodrigues", "Miriam Makeba", 
    "Luciano Pavarotti", "Tinariwen", "Kraftwerk", "Fela Kuti", 
    "Patsy Cline", "Björk", "Yo-Yo Ma"]
save_lyrics_to_csv(artist_list, max_songs=10)
df = pd.read_csv("artists_lyrics.csv")


all_chunks = []

# First, gather all chunks from all artists
for artist in artist_list:
    artist_df = df[df['Artist'] ==artist]
    combined_lyrics = ' '.join([ lyric for lyric in artist_df.Title_Lyrics])
    tokens = combined_lyrics.split()
    chunks = [' '.join(tokens[i:i+100]) for i in range(0, len(tokens), 100)]
    all_chunks.extend(chunks)
# # Now, fit the vectorizer on all chunks
vectorizer = TfidfVectorizer().fit(all_chunks)

# # Process each artist and transform their data with the common vectorizer
artist_vectors = {}
for artist in artist_list:
    print(f"Processing {artist}...")
    artist_vectors[artist] = get_artist_vector(artist, df, vectorizer)

# Compute cosine dissimilarity
#from itertools import combinations

# Generate all unique artist pairs from the artist list
# from itertools import combinations

# # Generate all unique artist pairs from the artist list
# artist_pairs = list(combinations(artist_list, 2))

# for artist1, artist2 in artist_pairs:
#     dissimilarity = 1 - cosine_similarity([artist_vectors[artist1]], [artist_vectors[artist2]])[0][0]
#     print(f"Cosine dissimilarity between {artist1} and {artist2}: {dissimilarity}")

def get_most_opposite_artist(target_artist, artist_vectors):
    max_dissimilarity = -1
    most_opposite = None
    
    for artist, vector in artist_vectors.items():
        if artist != target_artist:
            dissimilarity = 1 - cosine_similarity([artist_vectors[target_artist]], [vector])[0][0]
            if dissimilarity > max_dissimilarity:
                max_dissimilarity = dissimilarity
                most_opposite = artist
    
    return most_opposite
for artist in artist_list:
    opposite_artist = get_most_opposite_artist(artist, artist_vectors)
    print(f"The most opposite artist to {artist} is {opposite_artist}.")




# from gensim.models import KeyedVectors

# # Load the pre-trained Word2Vec model (It's huge: about 3.4 GB)

# import gensim.downloader as api

# Download and load the pre-trained Word2Vec model (about 1.6 GB)
# word2vec_model = api.load("word2vec-google-news-300")

# word2vec_model = KeyedVectors.load_word2vec_format(model_path, binary=True)

# def get_vector(text, model):
#     """Get the vector representation of a text using a word embedding model."""
#     words = text.split()
#     vector = np.zeros(model.vector_size)
#     num = 0
#     for word in words:
#         if word in model:
#             vector += model[word]
#             num += 1
#     if num > 0:
#         vector /= num
#     return vector

# artist_vectors = {}

# for artist in artist_list:
#     print(f"Processing {artist}...")
#     artist_data = genius.search_artist(artist, max_songs=10)
#     combined_lyrics = ' '.join([song.lyrics for song in artist_data.songs])
#     artist_vectors[artist] = get_vector(combined_lyrics, word2vec_model)

# from itertools import combinations

# for artist1, artist2 in combinations(artist_list, 2):
#     dissimilarity = 1 - cosine_similarity([artist_vectors[artist1]], [artist_vectors[artist2]])[0][0]
#     print(f"Cosine dissimilarity between {artist1} and {artist2}: {dissimilarity}")









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


# --------------------------


# playlists_df = pf.fetch_spotify_generated_playlists('aragaosm')
# playlists_df =playlists_df[playlists_df['owner']== 'Spotify']
# print(playlists_df)

# # Fetch audio features for the entire playlist list
# playlist_to_recommend = playlists_df.iloc[5]
# audio_features_dfs = pf.fetch_audio_features_for_playlists(playlists_df)

# recommendations = pf.get_opposite_playlist_recommendations(audio_features_dfs[5])
# print(recommendations)

# pf.create_playlist('aragaosm',playlist_to_recommend['name'],recommendations)


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
