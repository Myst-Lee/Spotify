import requests
import secrets
import urllib.parse
import random
import requests
import string
import pandas as pd
import base64
import spotipy
import json
import streamlit as st

from requests import post, get
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session

app = Flask(__name__)
secret_key = secrets.token_urlsafe(32)
app.secret_key = secret_key

CLIENT_ID = '12123248c69d4de5b7cd1b56e4cdd3a0'
CLIENT_SECRET = '3776097edd394860b335763fb0c78a77'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# Unique one time code
def id_generator(size=10, chars=string.ascii_uppercase + string.digits+ string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

def timedeltas(date_str1, date_str2):
    date_format = "%d/%m/%Y %H:%M:%S.%f"
    date1 = datetime.strptime(date_str1, date_format)
    date2 = datetime.strptime(date_str2, date_format)
    difference = date2 - date1
    return difference > timedelta(minutes=1) # 1 minutes diff

def generate_new_code(code_storage):
    code_storage = [arr for arr in code_storage if not timedeltas(arr[1], datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f'))]
    currentDateTime = datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f')
    new_code = id_generator()
    new_code_arr = [new_code, currentDateTime]
    code_storage.append(new_code_arr)
    return code_storage

def redeem_code(code_storage, in_code):
    code_storage = [arr for arr in code_storage if not timedeltas(arr[1], datetime.now().strftime('%d/%m/%Y %H:%M:%S.%f'))]
    code_storage = [arr for arr in code_storage if arr[0] != in_code]
    return code_storage

code_storage = []
# code_storage=generate_new_code(code_storage) generate code
# code_storage = redeem_code(code_storage, 'wWiMvro920') claim code

# Page TItle
st.set_page_config(
    page_title="Spotify Playlist",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Show Title
st.title("Spotify Interactive Playlist")

# Show readme
readme = st.checkbox("readme first")

if readme:
    st.write("xxxx")

sideb = st.sidebar

sideb.header("User Input Prompt")
sb = sideb.selectbox(
    'Select feature',
    ['Generate Code', 'Claim code']
)



@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'> Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email' #user-read-email

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog':True  #load login page every time
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    print("B")
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    print("A")
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data = req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/playlists')


@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        print("TOKEN EXPIRED. REFRESHING...")
        return redirect('/refresh_token')

    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers = headers)
    playlists = response.json()

    return jsonify(playlists)

@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        print("TOKEN EXPIRED. REFRESHING...")
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

    response = requests.post(TOKEN_URL, data = req_body)
    new_token_info = response.json()

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/playlists')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug = True)







