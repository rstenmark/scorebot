import sqlite3, paths
import discord.client
from typing import Any
def _setup():
    con, cur = open_db()
    cur.execute(f"""CREATE TABLE statistics (user_id INTEGER PRIMARY KEY ASC, guild_id INTEGER, score INTEGER)""")
    cur.execute(f"""CREATE TABLE messages (message_id INTEGER PRIMARY KEY ASC, guild_id INTEGER, author_id INTEGER, score INTEGER)""")
    con.commit()
    con.close()

def open_db():
    '''Returns open sqlite3 Connection and Cursor objects by unpacking
    them from the optional ConCur argument or by instantiating new objects'''
    con = sqlite3.connect(paths.database)
    cur = con.cursor()
    return con, cur

def is_empty(l: list):
    if len(l) == 0:
        return True
    else:
        return False

def get_id_exists(user_id: int, guild_id: int) -> bool:
    '''Returns True if user exists otherwise False'''
    con, cur = open_db()
    query = f"""SELECT * FROM statistics WHERE user_id = {user_id} AND guild_id = {guild_id}"""
    ret = cur.execute(query).fetchall()
    con.commit()
    con.close()
    return not is_empty(ret)

def get_score_by_id(user_id: int, guild_id: int) -> int:
    '''Returns number of score by username'''
    con, cur = open_db()
    if get_id_exists(user_id, guild_id):
        query = f"""SELECT score FROM statistics WHERE user_id = {user_id} AND guild_id = {guild_id}"""
        ret = cur.execute(query).fetchall()
        con.commit()
        con.close()
        return ret[0][0]
    else:
        return 0

def create_id(user_id: int, guild_id: int, score: int=0) -> Any:
    '''Creates a column with provided username and score (O by default).'''
    con, cur = open_db()
    query = f"""INSERT INTO statistics(user_id, guild_id, score) values ({user_id}, {guild_id}, {score})"""
    ret = cur.execute(query).fetchall()
    con.commit()
    con.close()
    return ret

def update_score_by_id(user_id: int, guild_id: int, score: int) -> Any:
    '''Updates a user's score'''
    con, cur = open_db()
    # New user
    if not get_id_exists(user_id, guild_id):
        print(f"Creating ID {user_id}, {guild_id}")
        ret = create_id(user_id, guild_id, score)
    else:
        # Update new score value for user
        print(f"Setting {user_id}'s score to {score}")
        query = f"""UPDATE statistics SET score = {score} WHERE user_id = {user_id} AND guild_id = {guild_id}"""
        ret = cur.execute(query).fetchall()
    con.commit()
    con.close()
    return ret

def increment_score_by_id(user_id: int, guild_id: int):
    '''Increments a user's score by 1'''
    update_score_by_id(
        user_id=user_id,
        guild_id=guild_id,
        score=get_score_by_id(user_id, guild_id) + 1
    )

def decrement_score_by_id(user_id: int, guild_id: int):
    '''Decrements a user's score by 1'''
    update_score_by_id(
        user_id=user_id,
        guild_id=guild_id,
        score=get_score_by_id(user_id, guild_id) - 1
    )

def get_high_score_by_guild(client: discord.client.Client, guild_id, limit=10):
    con, cur = open_db()
    query = f"""SELECT user_id, score FROM statistics WHERE guild_id = {guild_id} ORDER BY score"""
    result = cur.execute(query).fetchmany(limit)
    con.commit()
    con.close()
    ret = "**Heavenly and Auspicious social credit leaderboard**```"
    if is_empty(result):
        ret += "Nobody is credible here 。 A black cloud plumes above your home 。"
    else:
        for tuple in result:
            user = client.get_user(tuple[0])
            if not isinstance(user, type(None)):
                ret += f"{user.display_name}: {tuple[1]} points\n"
            else:
                ret += f"Unknown: {tuple[1]} points\n"
    ret += "```"
    return ret