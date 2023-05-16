import discord, paths, sqlite3
from typing import Any

def open_db():
    '''Returns open sqlite3 Connection and Cursor objects by unpacking
    them from the optional ConCur argument or by instantiating new objects'''
    con = sqlite3.connect(paths.database)
    cur = con.cursor()
    return con, cur

def get_id_exists(user_id: int, guild_id: int) -> bool:
    '''Returns True if user exists otherwise False'''
    con, cur = open_db()
    query = f"""SELECT user_id FROM statistics WHERE user_id = {user_id} and guild_id = {guild_id}"""
    ret = cur.execute(query).fetchall()
    con.commit()
    con.close()
    if len(ret) == 0:
        return False
    else:
        return True

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

def get_high_score_by_guild(client: discord.Client, guild_id, limit=10):
    con, cur = open_db()
    query = f"""SELECT user_id, score FROM statistics WHERE guild_id = {guild_id} ORDER BY score"""
    result = cur.execute(query).fetchmany(limit)
    con.commit()
    con.close()
    ret = "**Heavenly and Auspicious social credit leaderboard**```"
    print(result)
    if len(result) == 0:
        ret += "Nobody is credible here 。 A black cloud plumes above your home 。"
    else:
        for tuple in result:
            user = client.get_user(tuple[0])
            if not isinstance(user, type(None)):
                ret += f"{user.display_name}: {tuple[1]} points\n"
            else:
                ret += f"Unknown: {tuple[1]} points\n"
    ret += "```狗屎是神聖的 。"
    return ret

class MyClient(discord.Client):
    '''SocialCreditBot'''
    async def on_ready(self):
        print("Ready as", self.user)

    async def on_message(self, msg):
        if msg.content.startswith('!credit'):
            s = msg.content.split(" ")
            if len(s) != 1:
                await msg.channel.send("```Usage: !credit```")
            else:
                await msg.channel.send(get_high_score_by_guild(self, msg.guild.id))

    async def get_channel_messages(self, channel_name, limit=10):
        for c in self.get_all_channels():
            if c.name == channel_name:
                messages = [msg async for msg in c.history()]
        return messages

    async def _handle_reaction(self, payload: discord.RawReactionActionEvent):
        '''Determines what to do with a given Discord reaction'''
        
        # Get reacted message
        channel = self.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        #print(f"guild: {guild}\nchannel: {channel}\nmsg: {msg}\nreactor_id: {reactor_id}")

        # No score modifications when self reacting
        if payload.user_id != msg.author.id:
            print(f"{msg.author.name}'s score was {get_score_by_id(msg.author.id, msg.guild.id)} in guild {msg.guild.id}")
            match payload.event_type:
                case 'REACTION_ADD':
                    increment_score_by_id(msg.author.id, msg.guild.id)
                case 'REACTION_REMOVE':
                    decrement_score_by_id(msg.author.id, msg.guild.id)
                case _:
                    pass
            print(f"{msg.author.name}'s score now {get_score_by_id(msg.author.id, msg.guild.id)} in guild {msg.guild.id}")

    async def on_raw_reaction_add(
        self,
        payload: discord.RawReactionActionEvent
    ):
        print(payload)
        await self._handle_reaction(payload)

    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent
    ):
        print(payload)
        await self._handle_reaction(payload)