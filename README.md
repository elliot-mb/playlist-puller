# Playlist puller
After authenticating your Spotify and YouTube accounts, this script makes calls to both APIs to automatically copy playlists from Spotify to YouTube.
Each song title and artist of a selected Spotify playlist are searched (quota-cost free using the [Invidious API](https://docs.invidious.io/api/#get-apiv1videosid)), the most relevant result is then added to a newly-made YouTube playlist.\
\
With the [quota](https://developers.google.com/youtube/v3/determine_quota_cost) limit that the YouTube API has, this script can generate up to ~200 playlist entries per 24 hour period (even after mitigating the [search](https://developers.google.com/youtube/v3/docs/search/list#apps-script) cost originally present when just using the YouTube API).
## How can I use it?
I am working to turn this project into a web app, at which point the user will be able to simply authenticate with OAuth and use the app.\
\
Presently it operates on a **client secret** and OAuth authentication; currently users besides myself will not be able to use this, as they need the Google Cloud and Spotify API application secrets. This is not important however, since Google Cloud Platform applications mandate the verification of apps before general users can authenticate their email. Any and all users would need manually adding as **test users** which isn't viable (there is also a hard limit of 100 test users), and quota limits would puncture the usability of the app regardless of this. I may work on getting this app verified.\
\
This will give me the breathing space to put together a full web app, with a front end that makes request to my backend's API, which will sit on top of Invidious and Spotify and crunch the numbers instead of the client. The backend may use **FastAPI**, and the front, **React**. 
## Examples of usage
### Spotify interaction
<img src="https://user-images.githubusercontent.com/45922387/170982137-2b48f31a-446a-42f1-adff-4286257f815a.png" alt="image" width="700"/></img>
### YouTube safety
<img src="https://user-images.githubusercontent.com/45922387/170988636-fe998d9d-8b5f-4bb6-b616-6b8fa28db016.png" alt="image" width="700"/></img>
### Writing YouTube playlist
<img src="https://user-images.githubusercontent.com/45922387/170989727-70bca017-15cf-402c-9f88-c418037027d1.png" alt="image" width="700"/></img>
### Network outage tollerance 
<img src="https://user-images.githubusercontent.com/45922387/171198793-504eec38-29de-4e92-8322-f808b8924665.png" alt="image" width="700"/></img>
