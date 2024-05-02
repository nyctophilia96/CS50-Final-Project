import os
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

scope = ['user-top-read']

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

sp = Spotify(auth_manager = sp_oauth)

db = SQL("sqlite:///music.db")

def save_user_tokens_to_database(token_info):
    db.execute("INSERT OR REPLACE INTO users (spotify_access_token) VALUES (?)", token_info)

def get_user_top_tracks():
    top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')
    return top_tracks['items']

def get_user_top_artists():
    top_artists = sp.current_user_top_artists(limit=20, time_range='medium_term')
    return top_artists['items']

def get_recommendations():
    top_musics = get_user_top_tracks()
    seed_tracks = ','.join(top_musics)
    recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=30)
    return recommendations['tracks']

def create_playlist(track_uris):
    user_info = sp.current_user()
    user_id = user_info['id']
    playlist = sp.user_playlist_create(user_id, "Discover ur Feelings", public=True, collaborative=False)
    playlist_id = playlist['id']
    sp.playlist_add_items(playlist_id, track_uris)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/login")
def login():
    session.clear()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'])
    session['token_info'] = token_info
    save_user_tokens_to_database(token_info)
    return redirect("/")


@app.route("/top_artists")
def top_artists():
    if 'token_info' in session:
        top_artists = get_user_top_artists()
        return render_template('top_artists.html', top_artists=top_artists)
    else:
        return redirect(url_for('login'))

    
@app.route("/top_musics")
def top_musics():
    if 'token_info' in session:
        top_tracks = get_user_top_tracks()
        return render_template('top_musics.html', top_tracks=top_tracks)
    else:
        return redirect(url_for('login'))
    

@app.route("/recommender", methods=["GET", "POST"])
def recommender():
    if 'token_info' in session:
        if request.method == "POST":
            recommendations = get_recommendations()
            track_uris = [track['uri'] for track in recommendations]
            create_playlist(track_uris)
            return redirect(url_for('playlist_created'))
    
        else:
            recommendations = get_recommendations()
            return render_template('recommender.html', recommendations=recommendations)
    else:
        return redirect(url_for('login'))
    

@app.route("/playlist_created")
def playlist_created():
    if 'token_info' in session:
        return render_template('playlist_created.html')
    else:
        return redirect(url_for('login'))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")