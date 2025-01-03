import json
from Song import *
from dotenv import load_dotenv
import base64
from requests import post
from requests import get
from pytubefix import YouTube
import os
import logging
import sys

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
GOOGLE_API_KEY = "AIzaSyBHKd8FpWaOQ3cipdWRu6ihmclKMjXzaUQ"


def get_token():
    auth_string = CLIENT_ID + ":" + CLIENT_SECRET
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    spotify_url = "https://accounts.spotify.com/api/token"

    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    result = post(spotify_url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


def getAuthHeader():
    return {"Authorization": "Bearer " + token}


token = get_token()

playlist_url = "https://api.spotify.com/v1/users/monopoly_5000/playlists"

playlist_request = get(playlist_url, headers=getAuthHeader())

playlists = json.loads(playlist_request.text)
for playlist in playlists['items']:
    if playlist['name'] == 'Morning':
        found_playlist = playlist
        break

if found_playlist is None:
    sys.exit()
playlist_tracks = get(found_playlist['href'], headers=getAuthHeader())
playlist_tracks = json.loads(playlist_tracks.text)
tracks = playlist_tracks['tracks']['items']

# loading track dict from Track Dictionary file
f = open("Track Dictionary", "r")
track_dict = {}

line = f.readline().strip("\n")
while line != "":
    artist = f.readline().strip("\n")
    album = f.readline().strip("\n")
    length = f.readline().strip("\n")
    prompt = f.readline().strip("\n")
    url = f.readline().strip("\n")
    downloaded = f.readline().strip("\n")
    f.readline()
    song = Song(line, artist, album, length)
    song.set_downloaded(bool(downloaded))
    #song.set_downloaded(False)
    song.set_url(url)
    song.set_prompt(prompt)
    track_dict[line] = song
    line = f.readline().strip("\n")

f.close()

# updating track dict with songs from playlist
for track in tracks:
    if track['track']['name'] not in track_dict.keys():
        artists = ""
        for i in track['track']['artists']:
            artists += i['name'] + ", "
        artists = artists[:-2]
        song = Song(track['track']['name'], artists, track['track']['album']['name'], track['track']['duration_ms'])
        song.set_prompt(song.get_title() + " by " + song.get_artist())
        track_dict[song.get_title()] = song

# updating saved songs
for name in track_dict:
    found = False
    f = open("Saved Songs", "r")
    song = track_dict[name]
    for line in f:
        if line == (song.get_title() + " by " + song.get_artist()) or line == (
                song.get_title() + " by " + song.get_artist() + "\n"):
            found = True
            break
    f.close()

    if not found:
        f = open("Saved Songs", "a")
        f.write(song.get_title() + " by " + song.get_artist() + "\n")
        f.close()

# updating Track Dictionary file with new songs in track dict
for track in track_dict:
    found = False
    f = open("Track Dictionary", "r")
    for line in f:
        if line == (track + "\n"):
            found = True
            break
    f.close()
    if not found:
        f = open("Track Dictionary", "a")
        api_data = get("https://www.googleapis.com/youtube/v3/search", params={"part": "Snippet", "key": GOOGLE_API_KEY,
                                                                               "maxResults": 1,
                                                                               "q": track_dict[track].get_prompt(),
                                                                               "type": "video"})
        res = json.loads(api_data.text)
        link = "https://www.youtube.com/watch?v=" + res['items'][0]['id']['videoId']
        track_dict[track].set_url(link)
        f.write(track + "\n")
        f.write(track_dict[track].get_artist() + "\n")
        f.write(track_dict[track].get_album() + "\n")
        f.write(str(track_dict[track].get_length()) + "\n")
        f.write(track_dict[track].get_prompt() + "\n")
        f.write(link + "\n")
        f.write(str(track_dict[track].get_downloaded()) + "\n")
        f.write("-\n")


def download_song(name):
    yt = YouTube(track_dict[name].get_url(), on_progress_callback=print)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path="Song Files")
    ext = os.path.splitext(out_file)
    new_file = os.path.join("Song Files", name + '.mp3')
    os.rename(out_file, new_file)
    track_dict[name].set_downloaded(True)


for track in track_dict:
    if not track_dict[track].get_downloaded():
        download_song(track)

logging.basicConfig(filename="song_deletions.log", level=logging.ERROR)


def delete_song(song_title):
    try:

        if song_title in track_dict:
            del track_dict[song_title]

        with open("Track Dictionary", "r") as f:
            lines = f.readlines()
        with open("Track Dictionary", "w") as f:
            block_start = -1
            for i, line in enumerate(lines):
                if line.strip() == song_title:
                    block_start = i
                elif block_start != -1 and line.strip() == "-":
                    block_start = -1
                elif block_start == -1:
                    f.write(line)

        with open("Saved Songs", "r") as f:
            lines = f.readlines()
        with open("Saved Songs", "w") as f:
            for line in lines:
                song_info = line.strip().split(" by ")
                if song_info[0] != song_title:
                    f.write(line)

        song_filename = f"Song Files/{song_title}.mp3"
        if os.path.exists(song_filename):
            os.remove(song_filename)

    except FileNotFoundError:
        print(f"Error: File not found. Check if 'Track Dictionary' or 'Saved Songs' exists.")
    except PermissionError:
        print(f"Error: Permission denied. You might not have permission to modify the files.")
    except Exception as e:  # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")


f = open("Track Dictionary", "w")
for track in track_dict:
    f.write(track + "\n")
    f.write(track_dict[track].get_artist() + "\n")
    f.write(track_dict[track].get_album() + "\n")
    f.write(str(track_dict[track].get_length()) + "\n")
    f.write(track_dict[track].get_prompt() + "\n")
    f.write(track_dict[track].get_url() + "\n")
    f.write(str(track_dict[track].get_downloaded()) + "\n")
    f.write("-\n")
f.close()


def copy_to_text_file(file_name, dictionary):
    f = open(file_name, "w")
    for song in dictionary:
        f.write(dictionary[song].get_title() + "\n")  # Song Title
        f.write(dictionary[track].get_artist() + "\n")  # Artist
        f.write(dictionary[track].get_album() + "\n")  # Album
        f.write(str(dictionary[track].get_length()) + "\n")  # Length
        f.write(dictionary[track].get_prompt() + "\n")  # Prompt
        f.write(dictionary[track].get_url() + "\n")  # URL
        f.write(str(dictionary[track].get_downloaded()) + "\n")  # Downloaded
        f.write("-\n")  # Dash for spacing
    f.close()
