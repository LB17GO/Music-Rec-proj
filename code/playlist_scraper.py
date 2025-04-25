import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import time
import requests

# Replace with your Spotify Developer credentials
CLIENT_ID = "4cfd349ae4074bfaac40d9f498dd06ea"
CLIENT_SECRET = "d66a040acf3541c988b0b456f17938b1"

# This handles the access token part automatically
auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
token_info = auth_manager.get_access_token()
token = token_info['access_token']
headers = {
    'Authorization': f'Bearer {token}'
}

r = requests.get('https://api.spotify.com/v1/search?q=chill&type=playlist', headers=headers)
#print(r.json())
sp = spotipy.Spotify(auth_manager=auth_manager)




# Define search keywords for playlist discovery
SEARCH_KEYWORDS = [
    # Core genres
    "pop", "rock", "hip hop", "rap", "r&b", "country", "indie", "electronic", "metal", "jazz", "blues", "folk", "punk",
    
    # Sub-genres / niche
    "lofi", "synthwave", "trap", "edm", "drum and bass", "dubstep", "reggae", "k-pop", "j-pop", "afrobeats", "techno",

    # Moods / vibes
    "chill", "happy", "sad", "romantic", "moody", "energetic", "angry", "peaceful", "upbeat", "melancholy", "dark", "feel good",

    # Activities
    "study", "workout", "sleep", "party", "driving", "focus", "relax", "cleaning", "gaming", "background music",

    # Eras
    "70s", "80s", "90s", "2000s", "2010s", "2020s",

    # Situations
    "road trip", "rainy day", "sunny", "beach", "late night", "coffee shop", "club", "gym", "dinner", "wedding",

    # Playlists with personal or curated themes
    "favorites", "top hits", "underrated", "deep cuts", "new music", "throwback", "best of", "vibes", "bops", "anthems"
]

PLAYLIST_LIMIT_PER_KEYWORD = 10  # You can increase this
BASE_URL = "https://api.spotify.com/v1"
HEADERS = {
    "Authorization": f"Bearer {token}"
}

playlist_track_pairs = []

def get_playlist_tracks(playlist_id):
    tracks = []
    url = f"{BASE_URL}/playlists/{playlist_id}/tracks"
    params = {"limit": 100}

    try:
        while url:
            response = requests.get(url, headers=HEADERS, params=params)
            if response.status_code != 200:
                print(f"Failed to fetch tracks: {response.status_code}, {response.text}")
                break

            data = response.json()
            for item in data['items']:
                track = item.get('track')
                if track and track.get('id'):
                    tracks.append(track['id'])

            url = data.get('next')  # Spotify provides the next URL if paginated
            params = {}  # Ensure we don't send params again if using full next URL
    except Exception as e:
        print(f"Error fetching tracks for playlist {playlist_id}: {e}")
    
    return tracks


# Search and collect playlist-track data
for keyword in SEARCH_KEYWORDS:
    print(f"Searching playlists for keyword: {keyword}")
    try:
        search_url = f"{BASE_URL}/search"
        params = {
            "q": keyword,
            "type": "playlist",
            "limit": PLAYLIST_LIMIT_PER_KEYWORD
        }

        response = requests.get(search_url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Error searching playlists: {response.status_code}, {response.text}")
            continue

        playlists = response.json()['playlists']['items']
        for playlist in playlists:
            if playlist is None:
                continue
            playlist_id = playlist.get('id')
            if not playlist_id:
                continue

            track_ids = get_playlist_tracks(playlist_id)
            for track_id in track_ids:
                playlist_track_pairs.append({
                    "playlist_id": playlist_id,
                    "track_id": track_id
                })
            time.sleep(0.5)  # Pause to avoid rate limits
    except Exception as e:
        print(f"Error with keyword '{keyword}': {e}")









"""# Store playlist-track relationships
playlist_track_pairs = []
def get_playlist_tracks(playlist_id):
    tracks = []
    try:
        results = sp.playlist_items(playlist_id, additional_types=['track'], limit=100)
        while results:
            for item in results['items']:
                track = item.get('track')
                if track and track.get('id'):
                    tracks.append(track['id'])
            if results['next']:
                results = sp.next(results)
            else:
                break
    except Exception as e:
        print(f"Error fetching tracks for playlist {playlist_id}: {e}")
    return tracks

# Search and collect playlist-track data
for keyword in SEARCH_KEYWORDS:
    print(f"Searching playlists for keyword: {keyword}")
    try:
        search_results = sp.search(q=keyword, type='playlist', limit=PLAYLIST_LIMIT_PER_KEYWORD)
        playlists = search_results['playlists']['items']
        for playlist in playlists:
            playlist_id = playlist['id']
            track_ids = get_playlist_tracks(playlist_id)
            for track_id in track_ids:
                playlist_track_pairs.append({"playlist_id": playlist_id, "track_id": track_id})
            time.sleep(0.5)  # Pause to avoid rate limits
    except Exception as e:
        print(f"Error with keyword '{keyword}': {e}")"""

# Save results to CSV
df = pd.DataFrame(playlist_track_pairs)
df.to_csv("playlist_track_dataset.csv", index=False)
print("✅ Dataset saved as 'playlist_track_dataset.csv'")
