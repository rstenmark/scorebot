import discord, bot, paths, db

if not paths.database.is_file():
    db._setup()

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