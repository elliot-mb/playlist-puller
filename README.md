# Playlist puller
After authenticating your Spotify and YouTube accounts, this script makes calls to both APIs to automatically copy playlists from Spotify to YouTube.
Each song title and artist of a selected Spotify playlist are searched (quota-cost free using the [Invidious API](https://docs.invidious.io/api/#get-apiv1videosid)), the most relevant result is then added to a newly-made YouTube playlist.\
\
With the harsh [quota](https://developers.google.com/youtube/v3/determine_quota_cost) limit that the YouTube API imposesd on its users, this script can generate up to ~200 playlist entries per 24 hour period.
