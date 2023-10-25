import playlist_functions as pf


print("Beyond Recommendations")
username = input('Enter you username: ')

playlist_type = input(""" Which playlist woudl you like to get a recommendation from: 
               \n (m) - 'made for you'
               \n (p) - 'personal playlist' 
               \n (r) - 50 most recent musics you listened to \n
                """)

playlists = []
if playlist_type == 'm':
    playlists = pf.fetch_spotify_generated_playlists(username)

    for idx, playlist in playlists.iterrows(): 
        if playlist['owner'] == username:
            print("index",idx, playlist['name'],playlist['uri'],playlist['total_tracks'])

    

elif playlist_type == 'p':
    playlists = pf.fetch_user_playlists(username)

    for idx, playlist in playlists.iterrows(): 
        if playlist['owner'] == username:
            print("index",idx, playlist['name'],playlist['uri'],playlist['total_tracks'])


elif playlist_type == 'r':
    # i need to create the function for this first
    pass

