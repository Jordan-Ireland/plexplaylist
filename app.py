from flask import Flask, jsonify, render_template, request
from plexapi.server import PlexServer
from plexapi.library import ShowSection
import json
import os.path
from datetime import datetime, timedelta
import sys
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.background import BackgroundScheduler
import database_controller as db
import os

DEBUG = bool(os.environ.get('DEBUG', False))

app = Flask(__name__)

sched = BackgroundScheduler(daemon=True)

base_plex_url = "http://" + os.environ.get('PLEX_IP_ADDRESS', "0.0.0.0") + ":" + os.environ.get('PLEX_PORT', "32400")
plex_token = os.environ.get('PLEX_TOKEN')
plex = PlexServer(base_plex_url, plex_token)
sections = plex.library.sections()
allshows = []
allActualShows = {}
PLAYLIST_TITLE = os.environ.get('PLAYLIST_TITLE', "Daily Playlist")
SHOWS_TO_ADD = int(os.environ.get('PLAYLIST_SIZE', 20))
showsInData = []

def check_playlist_watched(regenerate = True):
    global allActualShows
    if(DEBUG):
        print("Checking if playlist was watched.", file=sys.stdout)
    playlist = db.get_current_playlist()
    episodes_to_add_back = []
    if(playlist is not None):
        for episode in playlist:
            dbepisode = db.get_episode_by_id(episode[0])
            try:
                actualEpisode = allActualShows[str(dbepisode[4])].episode(season=dbepisode[2], episode=dbepisode[3])
                lastViewedAt = actualEpisode.lastViewedAt
                if lastViewedAt and lastViewedAt >= datetime.now() - timedelta(days=1):
                    if(DEBUG):
                        print("Episode " + dbepisode[1] + " s" + str(dbepisode[2]) + " e" + str(dbepisode[3]) + " was watched.", file=sys.stdout)                
                    db.update_last_watched(episode[0], datetime.now().strftime("%Y%m%d"))
                    db.update_can_be_picked(episode[0], False)
                    db.remove_from_current_playlist(episode[0])
                else:
                    episodes_to_add_back.append(actualEpisode)
            except Exception as e:
                if(DEBUG):
                    print("Failed to get lastViewedAt, removing from playlist.", e, file=sys.stdout)              
                db.update_last_watched(episode[0], datetime.now().strftime("%Y%m%d"))
                db.remove_from_current_playlist(episode[0])
        if(regenerate):
            generatePlaylist(None)
        
        if(DEBUG):
            print("Done checking if items were watched.", file=sys.stdout)

sched.add_job(check_playlist_watched, trigger=CronTrigger(hour=os.environ.get('UTC_CHECK_HOUR', 15), minute=os.environ.get('UTC_CHECK_MINUTE', 0), second=os.environ.get('UTC_CHECK_SECOND', 0)))
sched.start()

for section in sections:
    if(type(section) == ShowSection):
        for show in section.all():
            id = show.key.rsplit("/", 1)[1]
            allActualShows[id] = show
            allshows.append({"title": show.title + " (" + str(show.year) + ")", "id": show.key.rsplit("/", 1)[1]})
        allshows = sorted(allshows, key=lambda x: x["title"])

@app.route('/')
def index():
    global allshows
    return render_template('index.html', shows=allshows)

@app.route("/getselectedshows", methods=['GET'])
def getselectedshows():
    showData = []
    
    show_in_db = db.get_shows()
    if(show_in_db is not None):
        for show_id in show_in_db:
            showData.append(db.get_data_by_id(show_id[0]))
    
    return jsonify(showData)

@app.route("/getshowdata", methods=['GET'])
def getshowdata():
    showId = request.args.get("showId")
    json = getShowById(showId)

    return jsonify([json])

def getShowById(show):
    if type(show) is not str:
        aShow = allActualShows[show['id']]
        isId = False
    else:
        aShow = allActualShows[show]
        isId = True
    
    json = {"id": aShow.key.rsplit("/", 1)[1], "title": aShow.title, "year": aShow.year, "seasons": []}
    
    for seasonIndex in range(len(aShow.seasons())):
        plex_season_index = aShow.seasons()[seasonIndex].index
        if isId:
            checked = True
        else:
            checked = show["seasons"][seasonIndex]["checked"]
            
        json["seasons"].append({"sIndex": plex_season_index, "checked": checked, "episodes": []})
        eIndex = 0
        for e in aShow.seasons()[seasonIndex].episodes():
            if isId:
                checked = True
            else:
                checked = show["seasons"][seasonIndex]['episodes'][eIndex]['checked']
            json["seasons"][seasonIndex]["episodes"].append({"eIndex": e.index, "checked": checked, "title": e.title})

            eIndex += 1
    return json

@app.route("/generateplaylist", methods=['POST'])
def addShowsToPlaylist():
    wantedShows = request.json
    wantedShowIds = []

    for show in wantedShows['shows']:
        aShow = allActualShows[show['id']]
        if(DEBUG):
            print("Adding: " + aShow.title, file=sys.stdout)
        wantedShowIds.append(show['id'])
        db.insert_show(show, aShow)
    
    dbShowIds = db.get_shows()
    removed_show_ids = []

    if(dbShowIds is not None):
        for show_id in dbShowIds:
            if str(show_id[0]) not in wantedShowIds:
                aShow = allActualShows[str(show_id[0])]
                if(DEBUG):
                    print("Removing: " + aShow.title, file=sys.stdout)
                db.remove_show(show_id[0])
                removed_show_ids.append(show_id[0])

    if(DEBUG):
        print("Done adding shows.", file=sys.stdout)
    db.clear_current_playlist()
    generatePlaylist(wantedShows)

    return jsonify({"message": "Added shows to playlist", "wantedShowIds": wantedShowIds, "removedShowIds": removed_show_ids})

@app.route("/regenerateplaylist", methods=['GET'])
def regeneratePlaylist():
    check_playlist_watched(False)
    db.clear_current_playlist()
    generatePlaylist(None)
    return getcurrentplaylist()

def generatePlaylist(wantedShows):
    if(DEBUG):
        print("Generating Playlist.", file=sys.stdout)
    playlist = db.get_current_playlist()
    if(playlist is None or len(playlist) < SHOWS_TO_ADD):
        if(playlist is None):
            amountNeeded = SHOWS_TO_ADD
        else:
            amountNeeded = SHOWS_TO_ADD - len(playlist)
        randomShows = db.get_random_episodes(amountNeeded)
        if(randomShows is None or len(randomShows) < amountNeeded):
            if(DEBUG):
                print("Not enough random episodes found. Refreshing episodes.", file=sys.stdout)
            db.reset_can_be_picked()
            amountNeeded = SHOWS_TO_ADD
            
        randomShows = db.get_random_episodes(amountNeeded)
        if(DEBUG):
            print("Got random episodes.", file=sys.stdout)
        for show in randomShows:
            db.add_to_current_playlist(show[0])

    if(DEBUG):
        print("Done Generating Playlist. Adding to Plex.", file=sys.stdout)        
    found_playlist = getPlaylist()

    items = found_playlist.items()
    if(items is not None and len(items) > 0):
        found_playlist.removeItems(items)
    
    aEpisodes = []
    dbEpisodes  = []
    
    playlist = db.get_current_playlist()
    if(playlist is None):
        return jsonify({"message": "No playlist found."})
    for show in playlist:
        dbEpisodes.append(db.get_episode_by_id(show[0]))

    for episode in dbEpisodes:
        try:
            if(DEBUG):
                print("Adding episode to playlist: " + episode[0] + " -- " + episode[1] + " s" + str(episode[2]) + " e" + str(episode[3]), file=sys.stdout)
            aEpisodes.append(allActualShows[str(episode[4])].episode(season=episode[2], episode=episode[3]))
        except Exception as e:
            if(DEBUG):
                print("Failed to add episode", e, file=sys.stdout)
    found_playlist.addItems(aEpisodes)

@app.route("/getcurrentplaylist", methods=['GET'])
def getcurrentplaylist():
    playlist = db.get_current_playlist()
    json = {"playlist": []}
    if(playlist is None):
        return jsonify(json)
    for show in playlist:
        json["playlist"].append(db.get_episode_by_id(show[0]))
    return jsonify(json)

def getSeasons(show):
    seasons = []
    for season in show.seasons():
        seasons.append(season)
    return seasons

def getEpisodes(season):
    episodes = []
    for episode in season.episodes():
        episodes.append(episode)
    return episodes

def getPlaylist():    
    found_playlist = None
    for playlist in plex.playlists():
        if playlist.title == PLAYLIST_TITLE:
            found_playlist = playlist

    if(found_playlist is None):
        found_playlist = plex.createPlaylist(PLAYLIST_TITLE)

    return found_playlist

if __name__ == '__main__':
    app.run(host=os.environ.get('HOST', "0.0.0.0"), port=os.environ.get('PORT', 5000))
