# Spotify Playlist Optimisation Project

## Introduction
As music providers have enabled music to become more personalised and widely available, listening to songs has become a part of my daily routine. I often create playlists for different moods and genres, from hip hop to lo-fi to acoustic. However each time I create a playlist, it takes time for me to order the songs so that there are smooth transitions between each track. Another aspect of music I enjoy is rediscovering old songs as it brings back nostalgia.
Using Spotify’s API, I decided to develop an algorithm to sort tracks in order to optimise the flow of songs in a playlist. I also pulled through and sorted my top twenty songs in any given period from my Spotify data, so I could ‘rewind time’ and bring back old memories. To optimise your Spotify playlist please follow the steps below.

For more information on the proccess please refer to the following article: https://medium.com/@afibannor/spotify-playlist-optimisation-and-discovering-your-music-history-4e2b1fbc5c29

## Access the Spotify API
Before we start you first need to access the Spotify API. To do this you start by setting up a Spotify Developer account. Here you can create a project and retrieve the client ID and client secret. You also need to set up a redirect URI to access the API, for this project I set this to http://localhost:8888/callback/.

## Locate the Spotify URI
Then locate the the Spotify URI of the playlist you would like to reorder. In Spotify Desktop, search for the playlist you would like to reorder and click the three dots under the playlist name. Click the Ctrl button your keyboard and click share. You can then copy the Spotify URI of the playlist

<img width="656" alt="image" src="https://user-images.githubusercontent.com/40894018/166327365-ff56ba84-9df6-4622-bcfb-96b86cc26a05.png">

## Run sp_playlist_optimisation.py
You will now be able to run sp_playlist_optimisation.py to optimise the order of any playlist. First change the creator and username variables to the playlist creator username and you Spotify username respectively. If you are reordering your own playlist, the creator and username will be the same. Lastly in the function create_ordered_playlist, update the Spotify URI to the URI of the playlist you would like to reorder.
