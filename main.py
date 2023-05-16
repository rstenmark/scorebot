import discord, bot, paths, sqlite3, os

if not paths.database.is_file():
    with sqlite3.connect(paths.database) as con:
        cur = con.cursor()
        query = """CREATE TABLE statistics (user_id int, guild_id int, score int)"""

secret = open(paths.secrets, 'r').read()
client = bot.MyClient(
    intents=discord.Intents(
        discord.Intents.guilds.flag
        | discord.Intents.guild_messages.flag
        | discord.Intents.guild_reactions.flag
        | discord.Intents.message_content.flag
        | discord.Intents.members.flag
    )
)
client.run(
    token=secret
)