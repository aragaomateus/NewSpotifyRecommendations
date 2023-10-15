# Spotify Hyper & Opposite Playlist Generator

## Description
The Spotify Hyper & Opposite Playlist Generator is a Python-based tool to generate hyper-focused and polar opposite playlists based on a user's Spotify "for you" playlist. The project uses the Spotify API to fetch relevant playlist and track data to analyze and generate new playlist recommendations.

## Requirements
- Python 3.8+
- Streamlit
- Requests
- Pandas
- Numpy
- python-dotenv
- Pickle

## Setup

1. **Environment Variables**: Before running the tool, ensure you have a `.env` file in the project root with the following variable:

   ```
   SPOTIFY_REFRESH_TOKEN=your_spotify_refresh_token
   ```

   Replace `your_spotify_refresh_token` with your actual Spotify refresh token.

2. **Python Dependencies**: Install the necessary python packages using pip:

   ```
   pip install requests pandas numpy python-dotenv streamlit
   ```

## Usage

1. **Fetching Spotify Data**: Utilize the functions provided in `playlist_functions.py` to fetch and process Spotify data.

2. **Streamlit App**: The provided `streamlit` app is an example UI that uses the functions from `playlist_functions.py`. You can run the app with:

   ```
   streamlit run your_app_filename.py
   ```

   Replace `your_app_filename.py` with the name of your streamlit script if it's different.

3. Enter your Spotify username in the Streamlit app and discover your hyper and opposite playlists!

## Features

1. **Caching**: Data is cached to reduce redundant API calls to Spotify, enhancing the efficiency of the application.

2. **Modularity**: The codebase is modular, allowing developers to easily expand or modify functionality.

3. **Recommendation Engine**: The core logic uses audio features to recommend hyper playlists and can be expanded for opposite playlist recommendations.

## Limitations

- Ensure your Spotify refresh token is valid. If the token is invalid, API requests will fail.
- The rate limit for the Spotify API is handled, but excessive requests in a short time might still cause the tool to pause its operation temporarily.

## Contributing
Feel free to fork this project, create a feature branch, and submit a pull request if you wish to contribute.

## License
This project is licensed under the MIT License.

---

You can customize the README further as per your needs. Adjust the filenames, paths, or descriptions as necessary.