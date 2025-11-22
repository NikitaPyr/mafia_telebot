import random
import sqlite3

def init_db():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER,
            username TEXT,
            role TEXT,
            mafia_vote INTEGER DEFAULT 0,
            citizen_vote INTEGER DEFAULT 0,
            voted INTEGER DEFAULT 0,
            dead INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles_dist (
            players INTEGER,
            role TEXT
        )
    """)
    con.commit()
    con.close()

def insert_player(player_id, username):
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO players (player_id, username, dead)
        VALUES (?, ?, 0)
    """, (player_id, username))
    con.commit()
    con.close()

def get_all_alive():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM players WHERE dead = 0")
    data = [row[0] for row in cur.fetchall()]
    con.close()
    return data

def players_amount():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM players WHERE dead = 0")
    count = cur.fetchone()[0]
    con.close()
    return count

def get_players_roles():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT player_id, role FROM players WHERE dead = 0")
    data = cur.fetchall()
    con.close()
    return data

def get_mafia_usernames():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM players WHERE role = 'mafia' AND dead = 0")
    data = [row[0] for row in cur.fetchall()]
    con.close()
    return data

def set_roles(players_count=None):
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT player_id FROM players WHERE dead = 0")
    player_ids = [row[0] for row in cur.fetchall()]
    num_players = len(player_ids)
    if num_players == 0:
        return
    num_mafias = max(1, int(num_players * 0.3))
    roles = ["mafia"] * num_mafias + ["citizen"] * (num_players - num_mafias)
    random.shuffle(roles)
    for player_id, role in zip(player_ids, roles):
        cur.execute("UPDATE players SET role = ? WHERE player_id = ?", (role, player_id))
    con.commit()
    con.close()

def vote(vote_type, username, player_id):
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM players WHERE username = ? AND dead = 0", (username,))
    can_vote = cur.fetchone()
    if can_vote:
        cur.execute(f"UPDATE players SET {vote_type} = {vote_type} + 1 WHERE username = ?", (username,))
        cur.execute("UPDATE players SET voted = 1 WHERE player_id = ?", (player_id,))
        con.commit()
        con.close()
        return True
    else:
        con.close()
        return False

def mafia_kill():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT MAX(mafia_vote) FROM players")
    max_votes = cur.fetchone()[0]
    cur.execute("SELECT username FROM players WHERE mafia_vote = ? AND dead = 0", (max_votes,))
    result = cur.fetchone()
    username_killed = 'unknown'
    if result and max_votes > 0:
        username_killed = result[0]
        cur.execute("UPDATE players SET dead = 1 WHERE username = ?", (username_killed,))
        con.commit()
    con.close()
    return username_killed

def clear(dead=False):
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    if dead:
        cur.execute("UPDATE players SET mafia_vote = 0, citizen_vote = 0, voted = 0, dead = 0")
    else:
        cur.execute("UPDATE players SET mafia_vote = 0, citizen_vote = 0, voted = 0")
    con.commit()
    con.close()

def citizens_kill():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT MAX(citizen_vote) FROM players WHERE dead = 0")
    max_votes = cur.fetchone()[0]
    username_killed = 'никого'
    if max_votes > 0:
        cur.execute("SELECT username FROM players WHERE citizen_vote = ? AND dead = 0", (max_votes,))
        result = cur.fetchone()
        if result:
            username_killed = result[0]
            cur.execute("UPDATE players SET dead = 1 WHERE username = ?", (username_killed,))
            con.commit()
    con.close()
    return username_killed

def check_winner():
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM players WHERE role = 'mafia' AND dead = 0")
    mafia_alive = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE dead = 0")
    total_alive = cur.fetchone()[0]
    con.close()
    citizens_alive = total_alive - mafia_alive
    if mafia_alive == 0:
        return "Горожане"
    elif mafia_alive >= citizens_alive:
        return "Мафия"
    else:
        return None

init_db()
