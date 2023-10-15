import pandas as pd
import numpy as np
import random as rd
from collections import defaultdict

df = pd.read_csv('average_audio_features1.csv', index_col=0)

# def find_opposite(artist_name, df, n=3, weights=None):
#     # Get the artist's features
#     artist_features = df.loc[artist_name]
    
#     # Scale features if required (use Min-Max scaling or Z-score normalization)
#     scaled_df = (df - df.min()) / (df.max() - df.min())
#     scaled_features = (artist_features - df.min()) / (df.max() - df.min())

#     # Compute distances using weighted Euclidean distance
#     if weights is None:
#         weights = np.ones(len(scaled_features))  # if weights aren't provided, use equal weights
#     distances = np.sqrt(((scaled_df - scaled_features) ** 2 * weights).sum(axis=1))
    
#     # Sort by distance and get the top n most distant artists
#     opposites = distances.sort_values(ascending=False).head(n).index.tolist()
    
#     return opposites

NUM_SIMULATIONS = 10000
from scipy.spatial.distance import cosine, cityblock

def find_opposite(artist_name, df, n=3, weights=None, metric="euclidean"):
    artist_features = df.loc[artist_name]
    
    # Scale features
    scaled_df = (df - df.min()) / (df.max() - df.min())
    scaled_features = (artist_features - df.min()) / (df.max() - df.min())
    
    if weights is None:
        weights = np.ones(len(scaled_features))

    # Compute distances using the provided metric
    if metric == "euclidean":
        distances = np.sqrt(((scaled_df - scaled_features) ** 2 * weights).sum(axis=1))
    elif metric == "manhattan":
        distances = ((scaled_df - scaled_features).abs() * weights).sum(axis=1)
    elif metric == "cosine":
        distances = scaled_df.apply(lambda x: cosine(x, scaled_features), axis=1)
    else:
        raise ValueError("Unsupported metric")
    
    opposites = distances.sort_values(ascending=False if metric != "cosine" else True).head(n).index.tolist()
    
    return opposites

METRICS = ["euclidean", "manhattan", "cosine"]
top_artists_by_metric = {metric: defaultdict(int) for metric in METRICS}

for metric in METRICS:
    for _ in range(NUM_SIMULATIONS):
        artist = rd.choice(df.index.unique())
        top_artists = find_opposite(artist, df, metric=metric)
        for top_artist in top_artists:
            top_artists_by_metric[metric][top_artist] += 1

    # Display top artists for each metric
    print(f"Top artists using {metric} metric:")
    
    sorted_top_artists = sorted(top_artists_by_metric[metric].items(), key=lambda x: x[1], reverse=True)
    
    # Calculate the average number of times an artist is chosen
    avg_freq = sum([freq for _, freq in sorted_top_artists]) / len(sorted_top_artists)
    
    # Count how many artists surpass the average
    above_avg_count = sum(1 for _, freq in sorted_top_artists if freq > avg_freq)
    
    for artist, freq in sorted_top_artists[:10]:  # Top 10
        print(f"{artist}: {freq} times")
    
    print(f"Number of artists chosen above average: {above_avg_count}")
    print("-------------------------------")
