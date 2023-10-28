import pandas as pd
import numpy as np
import random as rd
from collections import defaultdict

df = pd.read_csv('../data/artist_avg_features.csv', on_bad_lines='skip')

df.set_index('artist_id', inplace=True)

NUM_SIMULATIONS = 1000
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

    print('Average frequency:',avg_freq)
    
    print(f"Number of artists chosen above average: {above_avg_count}")
    print("-------------------------------")



# ---------------------------------------------------------

# import pandas as pd
# from scipy.spatial.distance import cosine


# def find_opposite(artist_ids, df, n=10):
#     """
#     Find n artists that are most opposite in audio features to the given artists.
    
#     Args:
#     - artist_ids (list): List of artist ids.
#     - df (DataFrame): Dataframe with average audio features.
#     - n (int): Number of opposite artists to return for each artist.
    
#     Returns:
#     - list: A list of artists that are most opposite to the given artists and common among them.
#     """    
#     all_opposites = []

#     for artist_id in artist_ids:
#         if artist_id not in df.index:
#             raise ValueError(f"Artist '{artist_id}' not found in dataframe.")

#         # Get the features of the specified artist
#         artist_features = df.loc[artist_id]

#         # Drop the specified artist from the DataFrame for comparison
#         comparison_df = df.drop(artist_id)

#         # Scale features
#         scaled_df = (comparison_df - df.min()) / (df.max() - df.min())
#         scaled_features = (artist_features - df.min()) / (df.max() - df.min())

#         # Compute cosine distances
#         distances = scaled_df.apply(lambda x: cosine(x, scaled_features), axis=1)

#         # Get the top n artists with the highest cosine distance (i.e., most opposite)
#         opposites = distances.nlargest(n).index.tolist()

#         all_opposites.append(set(opposites))

#     # Find intersection of opposite artists for all artist_ids
#     intersection_of_opposites = set.intersection(*all_opposites)
    
#     return list(intersection_of_opposites)



# # Example usage
# artist_ids = ["1Iy8JKDTXo8e9HmyTCaTOZ"]  # Replace with desired artist name
# print(find_opposite(artist_ids, df))



# ----------------  SIMULATIONS UPDATING ----------------
