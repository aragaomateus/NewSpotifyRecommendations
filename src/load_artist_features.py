import pandas as pd
import playlist_functions as pf
import time
import os
import random

ARTIST_IDS_FILE = "../data/artist_ids.txt"
USED_ARTIST_IDS_FILE = "../data/used_artist_ids.txt"


def main():
    artist_ids = set(pf.get_artist_ids_from_file(ARTIST_IDS_FILE))
    
    if os.path.exists(USED_ARTIST_IDS_FILE):
        used_artist_ids = set(pf.get_artist_ids_from_file(USED_ARTIST_IDS_FILE))
    else:
        used_artist_ids = set()

    remaining_artist_ids = list(artist_ids - used_artist_ids)
    sampled_artist_ids = random.sample(remaining_artist_ids, min(2000, len(remaining_artist_ids)))

    print(f"[DEBUG] Total artist IDs: {len(artist_ids)}")
    print(f"[DEBUG] Total used artist IDs: {len(used_artist_ids)}")
    print(f"[DEBUG] Remaining artist IDs to process: {len(remaining_artist_ids)}")
    print(f"[DEBUG] Processing {len(sampled_artist_ids)} random artist IDs this run.")

    avg_features_data = []

    for idx, artist_id in enumerate(sampled_artist_ids, 1):  # Start index from 1
        try:
            print(f"[DEBUG] Processing artist ID: {artist_id}")
            avg_features = pf.get_avg_features_for_artist(artist_id)
            avg_features['artist_id'] = artist_id
            if len(avg_features) < 19:
                print('skipped')
                continue
            else:
                print('saving')
                avg_features_data.append(avg_features)
                pf.save_used_artist_ids(artist_id,USED_ARTIST_IDS_FILE)
            
            # Save data every 250 artists
            if idx % 250 == 0:
                temp_df = pd.DataFrame(avg_features_data)
                temp_df.to_csv('../data/artist_avg_features.csv', mode='a', header=not os.path.exists('../data/artist_avg_features.csv'), index=False)
                avg_features_data.clear()  # Clear the list for the next batch
            time.sleep(2)  # Introduce a delay to avoid hitting the rate limit
        except Exception as e:
            print(f"[ERROR] Failed to process artist {artist_id}: {e}")

    # Save any remaining data
    if avg_features_data:
        temp_df = pd.DataFrame(avg_features_data)
        temp_df.to_csv('../data/artist_avg_features.csv', mode='a', header=not os.path.exists('../data/artist_avg_features.csv'), index=False)

    print(f"[DEBUG] Processed {len(sampled_artist_ids)} artists' features this run.")
 


if __name__ == "__main__":
    main()
    # print(get_avg_features_for_artist('3mLu6fOzdwzWf2wyfPqdUa'))
