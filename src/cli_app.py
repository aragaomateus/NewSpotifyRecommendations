import playlist_functions as pf
import os

def display_playlists(playlists):
    for idx, (i, playlist) in enumerate(playlists.iterrows()): 
        print("index", idx, playlist['name'], playlist['description'])

def get_recommendations(audio_features_df, recommendation_type):
    try:
        if recommendation_type == 'o':
            return pf.get_opposite_playlist_recommendations(audio_features_df, limit=30)
        elif recommendation_type == 'h':
            return pf.get_hyper_playlist_recommendations(audio_features_df, limit=30)
    except TypeError:
        print("Type Error")
        return pf.get_opposite_playlist_recommendations(audio_features_df, limit=30)

def handle_user_actions(username, playlist_type):
    if playlist_type not in ['m', 'p']:
        return
    
    if playlist_type == 'm':
        playlists = pf.fetch_spotify_generated_playlists(username)
        playlists = playlists[playlists['owner'] == 'Spotify']
    elif playlist_type == 'p':
        playlists = pf.fetch_user_playlists(username)
        playlists = playlists[playlists['total_tracks'] > 30]
    
    os.system('clear')
    display_playlists(playlists)
    
    index_to_generate = int(input('\nChoose the index of playlist you would like to get the recommendations from:'))
    playlist_to_recommend = playlists.iloc[index_to_generate]
    audio_features_df = pf.fetch_audio_features_for_playlist(playlist_to_recommend)
    
    recommendation_type = input(f"Which type of recommendation would you like to get for {playlist_to_recommend['name']} : \n(o) - 'Opposite'\n(h) - 'Hyper focused'\noption: ")
    recommendations = get_recommendations(audio_features_df, recommendation_type)
    
    print(recommendations)
    
    to_create_playlist = input('Would You like to create a playlist based on these recommendations?(y or n) ')
    if to_create_playlist == 'y':
        pf.create_playlist(username, playlist_to_recommend['name'], recommendations)

print("----------Beyond Recommendations----------------")
username = input('Enter your username: ')

playlist_type = input("""Which playlist would you like to get a recommendation from:
                        (m) - 'made for you'
                        (p) - 'personal playlist'
                        (r) - 50 most recent musics you listened to
                        (q) - for exiting
                        option: """)



handle_user_actions(username, playlist_type)

    # elif playlist_type == 'r':
    #     # i need to create the function for recent listened songs for this first
    #     pass

