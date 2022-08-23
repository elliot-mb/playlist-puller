#!/usr/bin/env python3

# http://localhost:8080/ for google
import google.oauth2.credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 
from googleapiclient.errors import HttpError

import pickle
import html
import os
import json

#for invidious
import requests 
import urllib
import time

from functools import reduce
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# consts
NEW_PLAYLIST = 50
PLAYLIST_ENTRY = 50
CHANNEL_LOOKUP = 1
DEFAULT_CONSOLE_WIDTH = 80
FAUX_USER = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:100.0) Gecko/20100101 Firefox/100.0'}

## general methods 

def safeNumberEntry(prompt, min, max):
  selection = None
  while(not inRangeInt(selection, min, max)):
    userInput = ""
    try:
      userInput = input(f"{prompt} [{min}-{max}]:\n")
      selection = int(userInput)
      if(not inRangeInt(selection, min, max)): 
        print(f"[{selection}] out of range.")
    except ValueError: 
      print(f"[{userInput}] is not an integer.")
      selection = None
  return selection

def inRangeInt(x, lo, hi):
  if(type(x) != type(0)): return False
  return (x >= lo and x <= hi)

def requestHandle(request):
  response = None
  while(response == None):
    try:
      response = requests.get(request, headers=FAUX_USER, timeout=10)
    except requests.Timeout:
      print(f"Timeout error for request <{request}>, retrying.")
      response = None
    except requests.exceptions.ConnectionError:
      print(f"You're not connected to the internet, request <{request}> failed. Retrying after 10 seconds.")
      response = None
      time.sleep(10)
      print("Retrying.")
  return response

## spotify methods

def getSpotify():
  return spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))

def spPrompt(sp):
  resultCurrentUser = sp.current_user()
  name = resultCurrentUser['display_name']
  id = resultCurrentUser['id']
  print(f"You're logged in as {name} on spotify, with account id [{id}].")

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

  selection = safeNumberEntry("Select a playlist by its number listed above", 1, count)

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

## youtube methods 

def ytGetChannelIdName(youtube): #only costs 1 quota unit to look up by ID :) 
  request = youtube.channels().list(part='snippet, id', mine=True)
  response = request.execute()
  return (response['items'][0]['id'], response['items'][0]['snippet']['title'])
# https://invidious.snopyta.org/api/v1/channels/playlists/channelid use this for searching for playlists that already exist

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
            print(credentials)
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
  #print(f"Searching '{keywords}'")
  keywords = urllib.parse.quote(keywords, safe='') #marks artists and song name slashes unsafe
  request = f"https://invidious.snopyta.org/api/v1/search?q={keywords}&fields=videoId%2Ctype%2Ctitle"
  #print(f"GET {request}")
  response = requestHandle(request)
  #print(f"Response: {response.status_code}")
  response = response.json(); video = None
  for result in response:
    if(result['type'] == 'video'): 
      video = result
      break

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
  repeat = True
  fails = 0
  while(repeat and fails < 10):
    try: 
      response = request.execute()
      repeat = False
    except HttpError as err:
      if err.resp.status in [500]:
        print("YouTube back end error status 500, retrying after 5 seconds...")
        fails+=1
        time.sleep(5)
      else:
        raise


def fillPlaylist(youtube, playlist, searchTerms):
  for i in range(0, len(searchTerms)):
    video = getRelevantVideo(searchTerms[i])
    playlistInsert(youtube, playlist, video)

def getPlaylists(channelId, playlistName): # list all playlists on our account
  print("Finding all playlists on your account.")
  titles = []
  response = dict(continuation='start')
  while(response['continuation']):
    continueString = "" if response['continuation'] == 'start' else f"&continuation={response['continuation']}"
    request = f"https://invidious.snopyta.org/api/v1/channels/{channelId}/playlists?fields=playlists(title),continuation{continueString}"
    response = requestHandle(request)
    response = response.json(); 
    for playlist in response['playlists']: 
      titles.append(playlist['title'])
  return titles

def spPlaylistPrintSettings():
  columns = safeNumberEntry("Enter the number of columns to display", 1, 10)
  return (columns, DEFAULT_CONSOLE_WIDTH // columns) 

if __name__ == '__main__':

  exit = False
  spShowPlaylists = True
  cost = 0 # youtube quota cost

  #youtube
  youtube = build("youtube", "v3", credentials=ytRecallCredentials(ytGetFlow("client_secret.json")))
  channelId, ytName = ytGetChannelIdName(youtube); cost += CHANNEL_LOOKUP
  #spotify
  spotify = getSpotify()
  #spotify api interactions
  spPrompt(spotify) #shows the user who they are logged in as on spotify

  while(not exit):
    playlists = spGetPlaylists(spotify) # refresh playlists from spotify 
    if(spShowPlaylists):
      columns, length = spPlaylistPrintSettings()
      print("All playlists currently saved to your account:")
      gridPrint(playlists['strings'], length=length, columns=columns)

    selection = selectPlaylist(playlists)
    spPlaylist = dict(name=playlists['names'][selection - 1], uri=playlists['uris'][selection - 1])
    searchTerms = getSearches(spotify, spPlaylist['uri'])

    #youtube api interactions 
    print(f"You're logged in as {ytName} on YouTube, with channel id [{channelId}].")
    ytPlaylists = getPlaylists(channelId, spPlaylist['name'])
    if spPlaylist['name'] in ytPlaylists: 
      print(f"{ytName} already has the playlist '{spPlaylist['name']}', cannot overwrite.")

    elif(input(f"Create/update the playlist '{spPlaylist['name']}'? (y/n)\n").lower() == "y"): 
      ytPlaylist = addPlaylist(youtube, spPlaylist['name'], private=False); cost += NEW_PLAYLIST #the main thing we care about of ytPlaylist is it's ID
      fillPlaylist(youtube, ytPlaylist, searchTerms); cost += PLAYLIST_ENTRY * len(searchTerms) #the costly part
      print(f"Playlist '{ytPlaylist['snippet']['title']}' fully built!")

    if(input("Refresh and choose another playlist? (y/n)\n").lower() != "y"): print("Quitting script."); exit = True
    elif(input("Show refreshed list of playlists? (y/n)\n").lower() != "y"): spShowPlaylists = False
    else: spShowPlaylists = True

  print(f"Youtube quota cost: {cost}")