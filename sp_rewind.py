# -*- coding: utf-8 -*-
"""
Created on Thu Aug  5 00:29:58 2021

@author: User
"""
import datetime
from glob import glob
from os.path import join, abspath
from os import getcwd
import spotipy
import pandas as pd
import numpy as np
from sklearn import preprocessing
import datetime as dt
import spotipy.util as util
import matplotlib.pyplot as plt
from itertools import cycle
from sklearn.cluster import MeanShift, estimate_bandwidth

from sp_playlist_optimisation import encode_fields, MSclustering, playlist_weighting, square_rooted, cosine_similarity, ordered_playlist, generate_new_playlist,create_ordered_playlist

##SETUP
cid ='#####'
secret ='#####'

username = 'annor999' 

token = util.prompt_for_user_token(
    username=username,
    scope='playlist-modify-public', 
    client_id=cid, 
    client_secret=secret, 
    redirect_uri="http://localhost:8888/callback/"
)
sp = spotipy.Spotify(auth=token)


##READ IN SPOTIFY HISTORY
#https://stackoverflow.com/questions/39568925/python-read-files-from-directory-and-concatenate-that
spotify_history = pd.DataFrame()
dir_path = "./MyData_Extended/"
full_path = join(abspath(getcwd()), dir_path, "*.json")
for file_name in glob(full_path):
    json_reader = pd.read_json(file_name)

    spotify_history = spotify_history.append(json_reader, ignore_index=True)

def clean_spotify_history(spotify_history):
    spotify_history['ts'] = pd.to_datetime(spotify_history['ts'], format='%Y-%m-%d').dt.date
    spotify_history = spotify_history.sort_values(by='ts')
    
    spotify_music_history = spotify_history[spotify_history['episode_name'].isna()]
    spotify_podcast_history = spotify_history[spotify_history['episode_name'].notna()]

    spotify_music_history = spotify_music_history[['ts', 'ms_played', 'master_metadata_track_name', 'master_metadata_album_artist_name',
           'master_metadata_album_album_name', 'spotify_track_uri']]

    return spotify_music_history

def music_period(music_hist, start_date, end_date):
    start_date = datetime.datetime.strptime(start_date,'%Y-%m-%d').date()
    end_date =  datetime.datetime.strptime(end_date,'%Y-%m-%d').date()
    mask = (music_hist['ts'] >= start_date) & (music_hist['ts'] <= end_date)
    time_period = music_hist[mask]
    return time_period

   
def rewind_time(my_spotify_history, start_date, end_date):
    spotify_music_history = clean_spotify_history(my_spotify_history)
    spotify_music_period = music_period(spotify_music_history, start_date, end_date)
    
    ##GET TOP SONGS
    spotify_music_period_2 = spotify_music_period[['master_metadata_track_name', 'master_metadata_album_artist_name',
           'master_metadata_album_album_name', 'spotify_track_uri']]
    
    spotify_music_period_grp = spotify_music_period_2.groupby(['master_metadata_track_name', 'master_metadata_album_artist_name',
           'master_metadata_album_album_name', 'spotify_track_uri']).size().reset_index(name='counts')
    
    spotify_music_period_grp = spotify_music_period_grp.sort_values(by='counts',ascending=False)
    
    if len(spotify_music_period_grp) < 20:
        spotify_music_period_top = spotify_music_period_grp.head(len(spotify_music_period_grp))
    else:
        spotify_music_period_top = spotify_music_period_grp.head(20)
    
    ##GET TRACK FEATURES
    spotify_music_period_top['track_id'] = spotify_music_period_top['spotify_track_uri'].str[14:]
    
    spotify_music_period_top.columns = ['track_name', 'artist', 'album', 'spotify_track_uri', 'counts', 'track_id']
    spotify_music_period_top.reset_index(inplace=True)
    playlist_period_features=pd.DataFrame()
    playlist_period_features[["artist","album","track_name", "track_id"]]= spotify_music_period_top[['artist', 'album', 'track_name', 'track_id']]
    playlist_period_features[["danceability","energy","key","loudness","acousticness","mode", "speechiness","instrumentalness","liveness","valence","tempo", "duration_ms","time_signature"]]=''
    
    i=0
    for track in playlist_period_features['track_id']:
        audio_features=sp.audio_features(track)[0]
        for feature in playlist_period_features.iloc[:,4:]:
            playlist_period_features[feature][i] = audio_features[feature]
        i+=1
    
    
    cts_fields = ["danceability","energy","loudness","acousticness","speechiness","instrumentalness","liveness","valence","tempo", "duration_ms"]
    discrete_fields = ['key','mode', 'time_signature']
    
    playlist_period_features[cts_fields] = playlist_period_features[cts_fields].astype(float)
    playlist_period_features[discrete_fields] = playlist_period_features[discrete_fields].astype(int)
        
    ##SORT TRACKS
    encoded_features=encode_fields(playlist_period_features)
    clustered_tracks=MSclustering(encoded_features,playlist_period_features)
    weighted_tracks=playlist_weighting(clustered_tracks)
    final_playlist=ordered_playlist(playlist_period_features,weighted_tracks)[0]
    
    spotify_new_playlist = sp.user_playlist_create(user = username, name = start_date +'_' + end_date + '_top_songs_api', public=True, collaborative=False, description='')
    return sp.user_playlist_add_tracks(username, spotify_new_playlist['id'], final_playlist['track_id'])

rewind_time(spotify_history,'2019-01-01','2019-06-30')



