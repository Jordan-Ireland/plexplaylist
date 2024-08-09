# Quick reference

Maintained by: [**Jordan-Ireland**](https://github.com/Jordan-Ireland)

**Where to file issues:** [https://github.com/Jordan-Ireland/plexplaylist/issues](https://github.com/Jordan-Ireland/plexplaylist/issues)

**Source code found at:** [https://github.com/Jordan-Ireland/plexplaylist](https://github.com/Jordan-Ireland/plexplaylist)

**What is PlexPlaylist?**
PlexPlaylist connects to your Plex library and automatically creates daily viewing playlists. The playlists are customizable via a local webpage, allowing you to easily add or remove shows, seasons, or individual episodes. The system refreshes daily, automatically removing watched episodes to keep your playlists up-to-date and tailored to your viewing habits.

**Background tasks**
PlexPlaylist will run 1 background task at 15:00 UTC *(default, see environment variables below)*. This will refresh the playlist and removed watched episodes.

**Environment Variables**
- `PLEX_IP_ADDRESS` IP Address of the Plex instance, default: 0.0.0.0
- `PLEX_PORT` Port of the Plex instance, default: 32400
- `PLEX_TOKEN` API Token of Plex, see below for details. **REQUIRED**
- `HOST` Host of this docker container image, default: 0.0.0.0
- `PORT` Post of this docker container image, default: 5000
- `PLAYLIST_TITLE` Plex playlist title to create or manage, default: Daily Playlist
- `PLAYLIST_SIZE` Size of the total number of episodes to keep on the playlist, default: 20
- `UTC_CHECK_HOUR` Hour of day to refresh the playlist, default: 15 (15:00)
- `UTC_CHECK_MINUTE` Minute of day to refresh the playlist, default: 0
- `UTC_CHECK_SECOND` Second of day to refresh the playlist, default: 0
- `DEBUG` If **True**, will output debug messages to the stdout of the container, default: False

[**How to find Plex Token**](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
