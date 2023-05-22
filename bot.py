import discord, paths, sqlite3
from db import *
from typing import Any

EMOJI_CHILLING = "chilling"
EMOJI_MINUSCHILLING = "minusChilling"

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
                print(f"{msg.author.display_name} used !credit")
                await msg.channel.send(get_high_score_by_guild(self, msg.guild.id))
        elif msg.content.startswith('!sync'):
            s = msg.content.split(" ")
            if len(s) != 1:
                await msg.channel.send("```Usage: !sync```")
            else:
                print(f"{msg.author.display_name} used !sync")
                await self.sync_score(msg.guild.id)

    async def sync_score(self, guild_id: int):
        con, cur = open_db()
        channels = set()

        # Get all uncategorized channels in target guild
        for channel in self.get_guild(guild_id).channels:
            if isinstance(channel, discord.TextChannel):
                channels.add(channel)
        # Get all channel categories in target guild
        for category in self.get_guild(guild_id).categories:
            # Get all text channels in category
            for channel in category.text_channels:
                channels.add(channel)

        for channel in channels:
            # Get last 100 messages in channel (async)
            for message in [msg async for msg in channel.history()]:
                print(message)
                # Select messages matching this message id
                query = f"""SELECT score FROM messages WHERE message_id = {message.id}"""
                ret = cur.execute(query).fetchall()
                if not is_empty(ret):
                    # One match, duplicate message (message_id is required to be unique)
                    # This is the score in local record
                    recorded_sum = ret[0][0]
                    # This is the score in remote record
                    remote_sum = self.get_message_score(message)
                    if recorded_sum != remote_sum:
                        # Local record differs from remote record, update table
                        query = f"""UPDATE messages SET score = {remote_sum} WHERE message_id = {message.id}"""
                        cur.execute(query)
                else:
                    # Zero matches, new message
                    remote_sum = self.get_message_score(message)
                    query = f"""INSERT INTO messages VALUES ({message.id}, {guild_id}, {message.author.id}, {remote_sum})"""
                    cur.execute(query)

        # Commit changes at this point
        con.commit()

        # Get all recorded messages from this guild
        sums = dict()
        messages = cur.execute(f"""SELECT author_id, score FROM messages WHERE guild_id = {guild_id}""").fetchall()
        for message in messages:
            try:
                sums[message[0]] += message[1]
            except KeyError:
                sums[message[0]] = message[1]

        for author_id, score in sums.items():
            update_score_by_id(author_id, guild_id, score)

        con.commit()
        con.close()

    def get_message_score(self, message: discord.Message) -> int:
        sum = 0
        for reaction in message.reactions:
            try:
                if reaction.emoji.name == EMOJI_CHILLING:
                    sum += reaction.count
                elif reaction.emoji.name == EMOJI_MINUSCHILLING:
                    sum -= reaction.count
            except:
                pass
        return sum

    async def _handle_reaction(self, payload: discord.RawReactionActionEvent):
        '''Determines what to do with a given Discord reaction'''
        # Get reacted message
        emoji = payload.emoji.name
        channel = self.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        #print(f"guild: {guild}\nchannel: {channel}\nmsg: {msg}\nreactor_id: {reactor_id}")

        # No score modifications when self reacting
        if payload.user_id != msg.author.id:
            print(f"{msg.author.display_name}'s score was {get_score_by_id(msg.author.id, msg.guild.id)} in guild {msg.guild.id}")
            match payload.event_type:
                case 'REACTION_ADD':
                    if emoji == EMOJI_CHILLING:
                        increment_score_by_id(msg.author.id, msg.guild.id)
                    elif emoji == EMOJI_MINUSCHILLING:
                        decrement_score_by_id(msg.author.id, msg.guild.id)
                case 'REACTION_REMOVE':
                    if emoji == EMOJI_MINUSCHILLING:
                        increment_score_by_id(msg.author.id, msg.guild.id)
                    elif emoji == EMOJI_CHILLING:
                        decrement_score_by_id(msg.author.id, msg.guild.id)
                case _:
                    pass
            print(f"{msg.author.display_name}'s score now {get_score_by_id(msg.author.id, msg.guild.id)} in guild {msg.guild.id}")

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