#!/usr/bin/env python3

# http://localhost:8080/ for google
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 

import pickle
import html
import os
import json

import requests #for invidious
import urllib

from functools import reduce
import spotipy
from spotipy.oauth2 import SpotifyOAuth

## spotify methods

def getSpotify():
  return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

def spPrompt(sp):
  resultCurrentUser = sp.current_user()
  name = resultCurrentUser['display_name']
  id = resultCurrentUser['id']
  print(f"You're logged in as your Spotify account {name} (id:{id}).")

def inRange(x, lo, hi):
  return (x >= lo and x <= hi)

# pretty print 🖨️
def gridPrint(elements, length, columns):
  truncate = "... "; suffix = len(truncate)
  for i, element in enumerate(elements):
    if len(element) > length - suffix:
      elements[i] = element[:length - suffix] + "... "
    else:
      elements[i] += (" " * ((length - len(element))))

  for i in range(0, len(elements), columns):
    row = ""
    for j in range(i, min(i + columns, len(elements))):
      row += elements[j]
    print(row)

def spGetPlaylists(sp):
  playlists = sp.user_playlists(sp.current_user()['id'], limit=50)

  plNames = []
  plURIs = []
  offset = 0
  strings = [] #just for gridPrinting

  while playlists:
    for i, playlist in enumerate(playlists['items']):
      plName = playlist['name']
      plURI = playlist['uri']
      offset = i + 1 + playlists['offset']
      plNames.append(plName)
      plURIs.append(plURI)
      string = ("%4d %s" % (offset, plName))
      strings.append(string)
    if playlists['next']:
      playlists = sp.next(playlists)
    else:
      playlists = None

  return dict(names=plNames, uris=plURIs, count=offset, strings=strings) #dict of the users spotify playlists which will be selected from

def selectPlaylist(playlists):
  names = playlists['names']
  uris = playlists['uris']
  count = playlists['count']

  selection = -1
  while(not inRange(selection, 1, count)):
    userInput = ""
    try:
      userInput = input(f"Select a playlist by its number listed above [1-{count}]:\n")
      selection = int(userInput)
      if(not inRange(selection, 1, count)): 
        print(f"[{selection}] out of range.")
    except ValueError: 
      print(f"[{userInput}] is not an integer.")
      selection = -1

  playlist = (names[selection - 1], uris[selection - 1])
  name, URI = playlist

  print(f"Selected [{name}, {URI}]")

  return selection

def getSearches(sp, uri):
  playlistItems = sp.playlist_items(uri)
  searchTerms = [] # will go on to form youtube search queries 

  while playlistItems:
    for i, item in enumerate(playlistItems['items']):
      #print(item)
      track = item['track']
      artists = reduce(lambda x, y: f"{x}, {y}",[artist['name'] for artist in track['artists']], "")[2:]
      title = track['name']
      query = f"{artists} {title}".replace(",","")
      searchTerms.append(query)
      offset = i + 1 + playlistItems['offset']
      #print("%4d %s - %s" % (offset, artists, title))
    if playlistItems['next']:
      playlistItems = sp.next(playlistItems)
    else:
      playlistItems = None

  return searchTerms

# print(queries)

"""
youtube integration
https://developers.google.com/youtube/v3/guides/implementation/playlists
https://developers.google.com/youtube/v3/guides/implementation/search

"""
# youtube methods 

#const
COST = 50

def ytGetFlow(secretLocation):
  if(secretLocation == None): raise ValueError("Please provide a location for client secrets to be read from.")
  return InstalledAppFlow.from_client_secrets_file(secretLocation, scopes=['https://www.googleapis.com/auth/youtube.force-ssl',
  'https://www.googleapis.com/auth/youtube'])

def ytOAuth(flow):
  # Use the client_secret.json file to identify the application requesting
# authorization. The client ID (from that file) and access scopes are required.
  flow.run_local_server(port=8080, prompt="consent",authorization_prompt_message="Complete Youtube OAuth screen.")
  credentials = flow.credentials
  with open(".ytcache", "wb") as fileWritable:
    pickle.dump(credentials, fileWritable)
  return credentials

# oAuth if needed, else reuse/refresh token 
def ytRecallCredentials(flow):
  credentials = None

  if(os.path.exists(".ytcache")):
    with open(".ytcache", "rb") as fileReadable: 
      try:
        credentials = pickle.load(fileReadable)
        if not credentials or not credentials.valid:
          if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing Youtube access token.")
            credentials.refresh(Request())
          else:
            print("Fetching new Youtube tokens.")
            credentials = ytOAuth(flow)
        else:
          print("Youtube credentials currently valid.")
      except EOFError:
        # no data in our pickle jar
        print("No previous YouTube authorisations found, launching local OAuth page.")
        credentials = ytOAuth(flow)
  else:
    print("Finding a place to put your Youtube access token.")
    open(".ytcache", "wb") # makes new file
    credentials = ytOAuth(flow)
    
  return credentials

def addPlaylist(youtube, name, private):
  print(f"Creating new playlist '{name}' on your account.")
  privacyStatus = None
  if(private): privacyStatus = "private"
  else: privacyStatus = "public"

  body = dict(
    snippet=dict(
      title=name,
      description=f'"{name}" was created automatically by Playlist-Puller (https://github.com/elliot-mb)'
    ),
    status=dict(
      privacyStatus=privacyStatus
    )
  )
  request = youtube.playlists().insert(
    part='snippet, status', 
    body=body
  )
  return request.execute()

def getRelevantVideo(keywords):
  #print(f"Searching {keywords}.")
  # request = youtube.search().list(
  #   part='snippet',
  #   type='video',
  #   q=keywords,
  #   order='relevance'
  # )
  # response = request.execute()
  # return response['items'][0] #most relevant result
  
  #must quicker and less costly than the youtube api 
  print(f"Searching '{keywords}'")
  keywords = urllib.parse.quote(keywords, safe='') #marks artists and song name slashes unsafe
  request = f"https://invidious.snopyta.org/api/v1/search?q={keywords}&fields=videoId%2Ctype%2Ctitle"
  headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'}
  print(f"GET {request}")
  response = requests.get(request, headers=headers)
  print(f"Response: {response.status_code}")
  response = response.json(); video = None
  for result in response:
    if(result['type'] == 'video'): 
      video = result
      break
  
  # return type of this method looks like this
  """
  {
    title=<title>
    id={
      kind=youtube#video
      videoId=<videoId>
    }
  }
  """

  return dict(
    title=video['title'],
    id=dict(
      kind="youtube#video", 
      videoId=video['videoId'] 
    )
  )

def playlistInsert(youtube, playlist, video):
  print(f"Adding video '{html.unescape(video['title'])}'.")
  body = dict(
    snippet=dict(
      playlistId=playlist['id'],
      resourceId=video['id']
    )
  )
  request = youtube.playlistItems().insert(
    part='snippet, id',
    body=body
  )
  response = request.execute()
  #print(response)
# main

def fillPlaylist(youtube, playlist, searchTerms):
  for i in range(0, len(searchTerms)):
    video = getRelevantVideo(searchTerms[i])
    playlistInsert(youtube, playlist, video)

if __name__ == '__main__':

  #youtube
  youtube = build("youtube", "v3", credentials=ytRecallCredentials(ytGetFlow("client_secret.json")))
  #spotify
  spotify = getSpotify()
  #spotify api interactions
  spPrompt(spotify) #shows the user who they are logged in as on spotify
  print("All playlists currently saved to your account:")
  playlists = spGetPlaylists(spotify)
  gridPrint(playlists['strings'], length=20, columns=4)
  selection = selectPlaylist(playlists)
  spPlaylist = dict(name=playlists['names'][selection - 1], uri=playlists['uris'][selection - 1])
  searchTerms = getSearches(spotify, spPlaylist['uri'])
  #youtube api interactions
  ytPlaylist = addPlaylist(youtube, spPlaylist['name'], private=False) #the main thing we care about of ytPlaylist is it's ID
  #print(getRelevantVideo(searchTerms[0]))
  fillPlaylist(youtube, ytPlaylist, searchTerms)
  cost = COST * (1 + len(searchTerms))
  print(f"Playlist '{ytPlaylist['snippet']['title']}' fully built!")
  print(f"Youtube quota cost: {cost}.")

