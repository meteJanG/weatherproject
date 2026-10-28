import base64
import requests
import os
import random
from dotenv import load_dotenv

load_dotenv()

client_id = os.environ.get("SPOTIFY_CLIENT_ID")
client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

def get_playlist(temp):
    auth_string = f"{client_id}:{client_secret}"
    auth_base64 = str(base64.b64encode(auth_string.encode("utf-8")), "utf-8")
    token_url = "https://accounts.spotify.com/api/token"
    
    token_result = requests.post(
        token_url,
        headers={
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )
    
    if token_result.status_code != 200:
        print("Token Hatası:", token_result.text)
        return None

    token = token_result.json().get("access_token")
    if not token:
        return None

    # Hava durumuna göre şarkı havuzları (Sen buradaki ID'leri çoğaltabilirsin)
    soguk_sarkilar = [
        "4cOdK2wGLETKBW3PvgPWqT", # Rick Astley - Never Gonna Give You Up
        "7qiZfU4dY1lWllzX7mPBI3", # Ed Sheeran - Shape of You
        "0VjIjW4GlUZAMYd2vXMi3b", # The Weeknd - Blinding Lights
    ]
    
    sicak_sarkilar = [
        "60nZcImufyMA1MKQY3dcCH", # Daft Punk - Get Lucky
        "2VxeLyX666F8uXCJ0dZF8B", # Avicii - Wake Me Up
        "6habFhsOp2NvshLv26DqMb", # Calvin Harris - Summer
    ]
    
    # Sıcaklığa göre havuz seç
    if temp < 20:
        secilen_id = random.choice(soguk_sarkilar)
    else:
        secilen_id = random.choice(sicak_sarkilar)

    track_url = f"https://api.spotify.com/v1/tracks/{secilen_id}"

    try:
        track_result = requests.get(
            track_url,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if track_result.status_code != 200:
            print(f"Spotify Hatası (Kod: {track_result.status_code}): {track_result.text}")
            return None

        track = track_result.json()

        return {
            "url": track["external_urls"]["spotify"],
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "image": track["album"]["images"][0]["url"]
        }

    except Exception as e:
        print("Sistem Hatası:", e)
        return None