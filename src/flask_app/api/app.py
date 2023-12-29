from flask import Flask, jsonify, request
import playlist_functions as pf
import os

app = Flask(__name__)

# @app.route('/',methods=['GET'])


@app.route('/display_playlists', methods=['GET'])
def api_display_playlists():
    username = request.args.get('username')
    playlist_type = request.args.get('playlist_type')
    playlists = handle_user_playlists(username, playlist_type)
    return jsonify(playlists)

@app.route('/get_recommendations', methods=['GET'])
def api_get_recommendations():
    playlist_index = int(request.args.get('playlist_index'))
    recommendation_type = request.args.get('recommendation_type')
    username = request.args.get('username')
    playlist_type = request.args.get('playlist_type')
    playlists = handle_user_playlists(username, playlist_type)
    playlist_to_recommend = playlists.iloc[playlist_index]
    audio_features_df = pf.fetch_audio_features_for_playlist(playlist_to_recommend)
    recommendations = get_recommendations(audio_features_df, recommendation_type)
    return jsonify(recommendations)

@app.route('/handle_user_actions', methods=['GET'])
def handle_user_playlists(username, playlist_type):
    if playlist_type not in ['m', 'p']:
        return jsonify({'error': 'Invalid playlist type'}), 400

    if playlist_type == 'm':
        playlists = pf.fetch_spotify_generated_playlists(username)
        playlists = playlists[playlists['owner'] == 'Spotify']
    elif playlist_type == 'p':
        playlists = pf.fetch_user_playlists(username)
        playlists = playlists[playlists['total_tracks'] > 30]

    return playlists

def get_recommendations(audio_features_df, recommendation_type):
    try:
        if recommendation_type == 'o':
            return pf.get_opposite_playlist_recommendations(audio_features_df, limit=30)
        elif recommendation_type == 'h':
            return pf.get_hyper_playlist_recommendations(audio_features_df, limit=30)
    except TypeError:
        return pf.get_opposite_playlist_recommendations(audio_features_df, limit=30)

if __name__ == '__main__':
    app.run(debug=True)
