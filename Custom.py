# -*- coding: utf-8 -*-
# Don't touch this stuff
import json
import os, operator, time, sys, datetime
import random
from dotenv import load_dotenv
from plexapi.server import PlexServer
from datetime import date, datetime
import random
load_dotenv(verbose=True)

baseurl = os.environ['PLEX_URL']
token = os.environ['PLEX_TOKEN']
plex = PlexServer(baseurl, token)

PLAYLIST_TITLE = "NightTime TV"
TAG = "NightTV"
NUM_TO_ADD = 20
TVSHOWS_LIBRARY = plex.library.section("TV Shows")

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)
    
while True:
    if os.path.exists('data.json') and datetime.now().hour != 9:
        continue
    
    print("Adding new episodes on ", datetime.now())
    data = {"last_ran": datetime.now(), "show_ids": [], "episode_list": [], "current_episodes": [], "remaining_episodes": []}
    if(os.path.exists("data.json")):
        with open("data.json") as file:
            d = json.load(file)
            #2023-11-04T23:55:24.037142
            data["last_ran"] = datetime.strptime(d["last_ran"], "%Y-%m-%dT%H:%M:%S.%f")
            data["show_ids"] = d["show_ids"]
            data["episode_list"] = d["episode_list"]
            data["current_episodes"] = d["current_episodes"]
            data["remaining_episodes"] = d["remaining_episodes"]

    if not TVSHOWS_LIBRARY.search(collection=TAG):
        print("No episodes found in",TAG,"collection.")
        quit()


    actual_tv_show = {}
    #loop over TV shows in that tag
    for tv_show in TVSHOWS_LIBRARY.search(collection=TAG):
        #if it doesn't exist in data['show_ids'] then it's new
        tv_show_id = tv_show.key.rsplit("/", 1)[1]
        actual_tv_show[tv_show_id] = tv_show
        if tv_show_id not in data['show_ids']:
            data['show_ids'].append(tv_show_id)
            #add all the episode IDS to the eqpisode list
            for episode in tv_show.episodes():
                data["episode_list"].append([tv_show_id, episode.seasonNumber, episode.index])
                #randomly insert new episodes into the remaining episodes
                if len(data["remaining_episodes"]) == 0:
                    data["remaining_episodes"].append([tv_show_id, episode.seasonNumber, episode.index])
                else:
                    data["remaining_episodes"].insert(random.randint(0, len(data["remaining_episodes"]) - 1), [tv_show_id, episode.seasonNumber, episode.index])

    not_watched = []
    for episode_data in data["current_episodes"]:
        episode = actual_tv_show[episode_data[0]].episode(season=episode_data[1], episode=episode_data[2])
        if not episode.lastViewedAt or episode.lastViewedAt <= data['last_ran']:
            #add to not watched
            not_watched.append(episode_data)
    data["current_episodes"] = not_watched

    #add more to it
    if len(data["current_episodes"]) < NUM_TO_ADD:
        found_playlist = None
        for playlist in plex.playlists(): # If the playlist already exists, remove all episodes from it.
            removelist = []
            if playlist.title == PLAYLIST_TITLE:
                found_playlist = playlist
                items = found_playlist.items()
                for i in items:
                    playlist.removeItem(i)

        # get num of episodes we need to add to equal the total we want
        need_to_add = NUM_TO_ADD - len(data["current_episodes"])
        #if we're out of episodes or have too few readd them and shuffle
        if len(data["remaining_episodes"]) == 0 or len(data["remaining_episodes"]) < need_to_add:
            data["remaining_episodes"] = data["episode_list"]
            random.shuffle(data["remaining_episodes"])

        #add however many we need
        data["current_episodes"].extend(data["remaining_episodes"][0:need_to_add])
        data['remaining_episodes'] = data['remaining_episodes'][need_to_add:-1]

        actual_episodes = []
        for episode_data in data['current_episodes']:
            actual_episodes.append(actual_tv_show[episode_data[0]].episode(season=episode_data[1], episode=episode_data[2]))

        playlist.addItems(actual_episodes)
    print("Successfully Added New Items")
    with open("data.json", 'w') as file:
        json.dump(data, file, cls=DateTimeEncoder)
    
    time.sleep(3500)