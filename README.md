# Playlist puller
After authenticating your Spotify and YouTube accounts, this script makes calls to both APIs to automatically copy playlists from Spotify to YouTube.
Each song title and artist of a selected Spotify playlist are searched (quota-cost free using the [Invidious API](https://docs.invidious.io/api/#get-apiv1videosid)), the most relevant result is then added to a newly-made YouTube playlist.\
\
With the harsh [quota](https://developers.google.com/youtube/v3/determine_quota_cost) limit that the YouTube API imposes on its users, this script can generate up to ~200 playlist entries per 24 hour period (even after mitigating the [search](https://developers.google.com/youtube/v3/docs/search/list#apps-script) cost originally present when just using the YouTube API).
## Examples of usage
### Spotify interaction
<img src="https://user-images.githubusercontent.com/45922387/170982137-2b48f31a-446a-42f1-adff-4286257f815a.png" alt="image" width="700"/></img>
### YouTube safety
<img src="https://user-images.githubusercontent.com/45922387/170988636-fe998d9d-8b5f-4bb6-b616-6b8fa28db016.png" alt="image" width="700"/></img>
### Writing YouTube playlist
<img src="https://user-images.githubusercontent.com/45922387/170989727-70bca017-15cf-402c-9f88-c418037027d1.png" alt="image" width="700"/></img>

