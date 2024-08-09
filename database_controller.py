import sqlite3
import datetime as dt

table_created = False

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect("data.db")        
        if(not table_created):
            create_table(conn)
    except Exception as e:
        print(e)
    return conn

def create_table(conn):
    cur = conn.cursor()
    try:
        cur.execute("CREATE TABLE IF NOT EXISTS shows (id INTEGER PRIMARY KEY, title TEXT, year INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS seasons (id INTEGER PRIMARY KEY AUTOINCREMENT, show_id INTEGER, season_number INTEGER, include INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY AUTOINCREMENT, show_id INTEGER, season_id INTEGER, episode_number INTEGER, title TEXT, include INTEGER, last_watched TEXT DEFAULT '19900101', can_be_picked INTEGER DEFAULT TRUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS current_playlist (id INTEGER PRIMARY KEY AUTOINCREMENT, episode_id INTEGER)")
        conn.commit()
        table_created = True
    except Exception as e:
        print(e)
    finally:
        cur.close()

def insert_show(show, aShow):
    conn = create_connection()
    cur = conn.cursor()
    try:
        is_show_in_db = cur.execute("SELECT COUNT(title) FROM shows WHERE id = ?", (show['id'],)).fetchone()[0] > 0
        if (is_show_in_db):
            update_show(show)
            return
        cur.execute("INSERT INTO shows (id, title, year) VALUES (?, ?, ?)", (show['id'], aShow.title, aShow.year))

        for season in show['seasons']:
            season_id = insert_season(conn, cur, show['id'], season)
            aSeason = aShow.season(season['sIndex'])
            if(season_id == -1):
                continue
            for episode in season['episodes']:
                e_title = aSeason.episode(episode = episode['eIndex']).title
                insert_episode(conn, cur, show['id'], season['sIndex'], episode, e_title)
        
        conn.commit()

    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def update_show(show):
    conn = create_connection()
    cur = conn.cursor()
    try:
        for season in show['seasons']:
            cur.execute("UPDATE seasons SET include = ? WHERE show_id = ? AND season_number = ?", (season['checked'], show['id'], season['sIndex']))
            for episode in season['episodes']:
                result = cur.execute("SELECT include FROM episodes WHERE show_id = ? AND season_id = ? AND episode_number = ?", (show['id'], season['sIndex'], episode['eIndex'])).fetchone()
                if(result is not None and result[0] != episode['checked']):
                    cur.execute("UPDATE episodes SET include = ? WHERE show_id = ? AND season_id = ? AND episode_number = ?", (episode['checked'], show['id'], season['sIndex'], episode['eIndex']))

        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def insert_season(conn, cur, show_id, season):
    try:
        cur.execute("INSERT INTO seasons (show_id, season_number, include) VALUES (?, ?, ?)", (show_id, season['sIndex'], season['checked']))
        return cur.lastrowid
    except Exception as e:
        print(e)

    return -1

def insert_episode(conn, cur, show_id, season_id, episode, title):
    try:
        cur.execute("INSERT INTO episodes (season_id, show_id, title, episode_number, include) VALUES (?, ?, ?, ?, ?)", (season_id, show_id, title, episode['eIndex'], episode['checked']))
    except Exception as e:
        print(e)

def update_last_watched(episode_id, last_watched):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE episodes SET last_watched = ? WHERE id = ?", (last_watched, episode_id))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def update_can_be_picked(episode_id, can_be_picked):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE episodes SET can_be_picked = ? WHERE id = ?", (can_be_picked, episode_id))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def reset_can_be_picked():
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE episodes SET can_be_picked = TRUE")
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def get_episode_by_id(episode_id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        episode = cur.execute("SELECT s.title, e.title, se.season_number, episode_number, s.id FROM episodes as e, shows as s, seasons as se WHERE e.id = ? AND s.id = e.show_id AND se.id = e.season_id", (episode_id,)).fetchone()
        return episode
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def get_random_episodes(amountNeeded):
    conn = create_connection()
    cur = conn.cursor()
    try:
        currentdt = dt.datetime.now().strftime("%Y%m%d")
        episodes = cur.execute("SELECT id, include FROM episodes WHERE include = TRUE AND can_be_picked = TRUE ORDER BY RANDOM() LIMIT ?", (amountNeeded,)).fetchall()
        return episodes
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def clear_current_playlist():
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM current_playlist")
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def add_to_current_playlist(episode_id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO current_playlist (episode_id) VALUES (?)", (episode_id,))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def remove_from_current_playlist(episode_id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM current_playlist WHERE episode_id = ?", (episode_id,))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def get_current_playlist():
    conn = create_connection()
    cur = conn.cursor()
    try:
        playlist = cur.execute("SELECT episode_id FROM current_playlist").fetchall()
        return playlist
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def get_shows():
    conn = create_connection()
    cur = conn.cursor()
    try:
        shows = cur.execute("SELECT id FROM shows").fetchall()
        return shows
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def get_data_by_id(show_id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        json = {"seasons": []}
        show = cur.execute("SELECT id, title, year FROM shows WHERE id = ?", (show_id,)).fetchone()
        json['id'] = show[0]
        json['title'] = show[1]
        json['year'] = show[2]
        seasons = cur.execute("SELECT season_number, include, id FROM seasons WHERE show_id = ?", (show_id,)).fetchall()
        for season in seasons:
            season_json = {"sIndex": season[0], "checked": season[1], "episodes": []}
            episodes = cur.execute("SELECT episode_number, include, title FROM episodes WHERE show_id = ? AND season_id = ?", (show_id, season[2],)).fetchall()
            for episode in episodes:
                episode_json = {"eIndex": episode[0], "checked": episode[1], "title": episode[2]}
                season_json['episodes'].append(episode_json)
            json['seasons'].append(season_json)
        return json
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()

def remove_show(show_id):
    conn = create_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM shows WHERE id = ?", (show_id,))
        cur.execute("DELETE FROM seasons WHERE show_id = ?", (show_id,))
        cur.execute("DELETE FROM episodes WHERE show_id = ?", (show_id,))
        conn.commit()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()