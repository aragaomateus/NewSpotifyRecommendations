import playlist_functions as pf
import os

print("Beyond Recommendations")
username = input('Enter you username: ')

playlist_type = input(""" Which playlist woudl you like to get a recommendation from:\n
                          (m) - 'made for you'\n
                          (p) - 'personal playlist'\n
                          (r) - 50 most recent musics you listened to \n
                            option: """)

playlists = []
if playlist_type == 'm':
    playlists = pf.fetch_spotify_generated_playlists(username)
    os.system('clear')

    for idx, playlist in playlists.iterrows(): 
        print("index",idx, playlist['name'],playlist['uri'])
    index_to_generate = input('Choose the index of playlist you woudl like to get the recomendations from:')

    recommendation_type = input(""" Which type of recomendation would you like to get: \n 
                                (o) - 'Opposite'\n
                                (h) - 'Hyper focused'\n
                                option: """)                                  

    
elif playlist_type == 'p':
    playlists = pf.fetch_user_playlists(username)
    os.system('clear')

    for idx, playlist in playlists.iterrows(): 
        if playlist['owner'] == username:
            print("index",idx, playlist['name'],playlist['uri'],playlist['total_tracks'])


elif playlist_type == 'r':
    # i need to create the function for recent listened songs for this first
    pass

