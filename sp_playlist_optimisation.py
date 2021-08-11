# -*- coding: utf-8 -*-
"""
Created on Sat Jun 26 17:28:51 2021

@author: User
"""
import spotipy
import pandas as pd
import numpy as np
from sklearn import preprocessing
import datetime as dt
import spotipy.util as util
import matplotlib.pyplot as plt
from itertools import cycle
from sklearn.cluster import MeanShift, estimate_bandwidth

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


##GET PLAYLIST
def get_playlist_data(creator, playlist_uri):
    
    #Create empty dataframe
    playlist_features_list = ["artist","album","track_name", "track_id", "popularity", "danceability","energy","key","loudness","acousticness","mode", "speechiness","instrumentalness","liveness","valence","tempo", "duration_ms","time_signature"]
    
    playlist_df = pd.DataFrame(columns = playlist_features_list)
    
    #Loop through every track in the playlist, extract features and append the features to the playlist df
    
    playlist = sp.user_playlist_tracks(creator, playlist_uri)["items"]
    for track in playlist:
        #Create empty dict
        playlist_features = {}
        #Get metadata
        try:
            playlist_features["artist"] = track["track"]["album"]["artists"][0]["name"]
            playlist_features["album"] = track["track"]["album"]["name"]
            playlist_features["track_name"] = track["track"]["name"]
            playlist_features["track_id"] = track["track"]["id"]
            playlist_features["popularity"] = track["track"]["popularity"]  
        except TypeError:
            pass
        
        #Get audio features
        try:
            audio_features = sp.audio_features(playlist_features["track_id"])[0]
            for feature in playlist_features_list[5:]:
                playlist_features[feature] = audio_features[feature]
            
            #Concat the dfs
            track_df = pd.DataFrame(playlist_features, index = [0])
            playlist_df = pd.concat([playlist_df, track_df], ignore_index = True)
        except:
            pass
        
        playlist_df = playlist_df.astype({'popularity': 'int', 'key': 'int', 'mode': 'int', 'instrumentalness': 'float64','duration_ms': 'int', 'time_signature': 'int'})
    return playlist_df



###FEATURES 
def encode_fields(playlist_data):
    cts_encode_fields = [
        'danceability',
        'energy',
        'loudness',
        'acousticness',
        'speechiness',
        'instrumentalness',
        'liveness',
        'valence',
        'tempo',
        
    ]
    
    discrete_encode_fields = [
        'time_signature',
        'mode'
    ]
    
    ##Standard Scalar on continuous features 
    df_cluster = playlist_data[cts_encode_fields]
    
    X_cts = np.array(df_cluster)
    scaler = preprocessing.StandardScaler()
    scaler.fit(X_cts)
    X_cts = scaler.transform(X_cts)

    
    X_discrete = np.array(playlist_data[discrete_encode_fields])
    
    X_full= np.hstack((X_cts,X_discrete))
    return X_full
    

##CLUSTERING

##MEAN-SHIFT CLUSTERING
def MSclustering(playlist_features, playlist_data):
    X = playlist_features
    #The bandwidth can be automatically detected using
    bandwidth = estimate_bandwidth(X, quantile=0.2, n_samples=500)
    ms = MeanShift(bandwidth=bandwidth)
    ms.fit(X)
    labels = ms.labels_
    cluster_centers = ms.cluster_centers_
    
    labels_unique = np.unique(labels)
    n_clusters_ = len(labels_unique)
    
    print("number of estimated clusters : %d" % n_clusters_)
    #Plot result
    plt.figure(1)
    plt.clf()
    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, col in zip(range(n_clusters_), colors):
        my_members = labels == k
        cluster_center = cluster_centers[k]
        plt.plot(X[my_members, 0], X[my_members, 1], col + '.')
        plt.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=14)
    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

    labels = labels.reshape(len(labels), 1)
    X_ms_clustered = np.hstack((X,labels))
    
    cts_encode_fields = [
        'danceability',
        'energy',
        'loudness',
        'acousticness',
        'speechiness',
        'instrumentalness',
        'liveness',
        'valence',
        'tempo',
        ]
    
    discrete_encode_fields = [
        'time_signature',
        'mode'
    ]
        
    playlist_data_features= pd.DataFrame()
    playlist_data_features[cts_encode_fields + discrete_encode_fields +['cluster']]  = ''
    X_ms_clustered_df = pd.DataFrame(X_ms_clustered)
    
    playlist_data_features[cts_encode_fields + discrete_encode_fields +['cluster']] = X_ms_clustered_df
    playlist_data['cluster'] = pd.DataFrame(labels)
    
    #One hot encoding on CLuster field
    playlist_data_features = pd.get_dummies(playlist_data_features, columns = ['cluster'], dtype='int')
    return playlist_data_features




def playlist_weighting(playlist_data_features):
    playlist_data_features['acousticness'] = playlist_data_features['acousticness']*3.4 
    playlist_data_features['energy'] = playlist_data_features['energy']*1.17 
    playlist_data_features['tempo'] = playlist_data_features['tempo']*1.035
    return playlist_data_features



##COSINE SIMILARITY
def square_rooted(x):
   return np.sqrt(sum([a*a for a in x]))

def cosine_similarity(x,y):
 numerator = sum(a*b for a,b in zip(x,y))
 denominator = square_rooted(x)*square_rooted(y)
 return numerator/float(denominator)

#similarity_check = playlist_data_features
#print (cosine_similarity(similarity_check.loc[16], similarity_check.loc[18]))

def ordered_playlist(playlist_data, playlist_final_features):
    all_new_playlists_dic = {}
    for index_a, row_a in playlist_final_features.iterrows():
        print('first song: ', index_a)
        remaining_tracks = playlist_final_features
        index_b=index_a
        new_track_order=[index_a]
        scores=[]
        counter = 0
        while index_b < len(playlist_final_features):
            remaining_tracks = remaining_tracks.drop([index_b])
            all_scores=[]
            all_scores_dic={}
            counter+=1
            for index_c, row_c in remaining_tracks.iterrows():
                score = cosine_similarity(playlist_final_features.loc[index_b], remaining_tracks.loc[index_c])
                all_scores.append([index_b, index_c, score])
                all_scores_dic[index_c]=score
            print(all_scores_dic)   
            print("counter: ", counter)
            if counter == len(playlist_final_features):
                scores.append(0)
                break
            similar_song = max(all_scores_dic, key=all_scores_dic.get)
            max_score = max(all_scores_dic.values())
            print("similar song: ", similar_song)
            new_track_order.append(similar_song)
            scores.append(max_score)

            index_b = similar_song
        tracks_scores_df = pd.DataFrame(data={'new_order': new_track_order, 'score': scores })
        avg_score = np.mean(scores[:-1])
        tracks_scores_df['avg_score'] = avg_score
        all_new_playlists_dic[index_a]=tracks_scores_df

    
    all_avg_scores = []
    for first_track in all_new_playlists_dic:
        all_avg_scores.append(all_new_playlists_dic[first_track]['avg_score'][0])
    
    best_first_track = all_avg_scores.index(max(all_avg_scores))
    best_order = all_new_playlists_dic[best_first_track]['new_order']
    best_order_score = all_new_playlists_dic[best_first_track]['avg_score'][0]
    
    new_playlist_tracks = pd.merge(best_order, playlist_data, right_index=True, left_on='new_order')
    new_playlist_tracks = new_playlist_tracks.drop(columns=['new_order'])
    return new_playlist_tracks, best_order_score


##GENERATE PLAYLIST
def generate_new_playlist(username, original_playlist_uri, new_playlist_tracks):
    original_playlist = sp.user_playlist(user=username, playlist_id=original_playlist_uri, fields="name")
    playlist_name = original_playlist["name"]
    timestamp = dt.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
    spotity_new_playlist = sp.user_playlist_create(user = username, name = playlist_name + '_api_gen_' + timestamp, public=True, collaborative=False, description='')
    
    return sp.user_playlist_add_tracks(username, spotity_new_playlist['id'], new_playlist_tracks['track_id'])



##FINAL DEFINTION
def create_ordered_playlist (creator, username, playlist_uri):
    playlist_data = get_playlist_data(creator= creator, playlist_uri=playlist_uri)
    playlist_features = encode_fields(playlist_data)
    playlist_clustered = MSclustering(playlist_features, playlist_data)
    playlist_final_features = playlist_weighting(playlist_clustered)
    new_playlist_tracks = ordered_playlist(playlist_data, playlist_final_features)[0]
    return generate_new_playlist(username = username, original_playlist_uri = playlist_uri, new_playlist_tracks = new_playlist_tracks )

# playlist_data = get_playlist_data(creator= 'annor999', playlist_uri='spotify:playlist:2x9lf6o8ISHYsBQ5lJQm5J')
# playlist_features = encode_fields(playlist_data)
# playlist_clustered = MSclustering(playlist_features, playlist_data)
# playlist_final_features = playlist_weighting(playlist_clustered)
# new_playlist_data = ordered_playlist(playlist_data, playlist_final_features)
# new_playlist_tracks = new_playlist_data[0]
# new_playlist_score = new_playlist_data[1]

if __name__=="__main__":
    create_ordered_playlist('annor999', 'annor999', 'spotify:playlist:2x9lf6o8ISHYsBQ5lJQm5J')
 

#hip hop
#spotify:playlist:1Dy3dgDtSDQNjxLk5e9Y2S

#hip hop - james bay test
#spotify:playlist:256bDWMdloMHhjzpORnjIp

#chill pop  
#spotify:playlist:5DQ3f0k7BHIifAjBVul6n1

#chill
#spotify:playlist:5HBRMtp0uZqgaoNTIdBdLS

#pink 
#spotify:playlist:2tDK67WWjjc8ilYsNXyz6e

#chance & frank
#spotify:playlist:2sZcybDriXaIHV2g3fnE7e

#sundown
#spotify:playlist:2x9lf6o8ISHYsBQ5lJQm5J
