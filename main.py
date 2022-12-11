from naff import Client, Intents, listen
from dotenv import load_dotenv
import os

bot = Client(intents=Intents.DEFAULT | Intents.GUILD_MEMBERS | Intents.PRIVILEGED | Intents.ALL | Intents.MESSAGES)
load_dotenv()

@listen()
async def on_ready():
    print("┏ Guilds:")
    for guild in bot.guilds:
        print(f"┣ {guild.name}, {guild.id}")
    print("┗ Bot is connected to gateway")


bot.load_extension(name="extensions.reminders")
bot.load_extension(name="extensions.tasks")
bot.load_extension(name="extensions.config")
bot.load_extension(name="extensions.message_events")
bot.start(os.getenv("DISCORD_TOKEN"))
