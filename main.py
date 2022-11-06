from naff import Client, Intents, listen
from dotenv import load_dotenv
import os

bot = Client(intents=Intents.DEFAULT | Intents.GUILD_MEMBERS | Intents.PRIVILEGED | Intents.ALL | Intents.MESSAGES)
load_dotenv()

@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")



bot.load_extension(name="extensions.reminders")
bot.load_extension(name="extensions.tasks")
bot.load_extension(name="extensions.config")
bot.start(os.getenv("DISCORD_TOKEN"))
