from naff import Task, IntervalTrigger, Extension, listen
import re
import json

class Tasks(Extension):
    print("Tasks extension loaded")

    # * When bot is ready start our tasks
    @listen()
    async def on_ready(self):
        self.dehoist.start()

    # * Dehoist users by adding invisible characters to the front of their name
    @Task.create(IntervalTrigger(minutes=30))
    async def dehoist(self):
        # * Get the config from the config.json file
        config = json.load(open("config.json", "r"))
        for guild in self.bot.guilds:
            # * get this guild's config options
            try:
                guild_config = config["guilds"][str(guild.id)]
            except KeyError: # ! guild doesn't have a config set yet
                continue
            if guild_config["dehoisting"]:
                await guild.chunk_guild()
                pattern = re.compile("\W")
                count = 0
                print(f"┏ Alright! Scanning and changing nicknames in {guild.name}")
                for x in guild.members:
                    if x.bot: # ! Don't worry about bots
                        continue
                    if x.display_name[0] == "\u17b5": # ! Don't re-dehoist users
                        print(f"┣ Skipping {x.display_name} as their name wouldn't change")
                        continue
                    if re.sub(pattern, "", x.display_name[0]) == "":
                        print(f"┗ Changing {x.display_name}'s name")
                        try:
                            pnick = x.display_name
                            newnick = "\u17b5" + pnick
                            await x.edit_nickname(
                                new_nickname=newnick,
                                reason=f"Automatic dehoist - Toggle this with /config",
                            )
                            count += 1
                        except Exception as e:
                            print(e)

                if count != 0:
                    print(f"┗ Changed **{count}** nicknames.")
                else:
                    print(f"┗ No nicknames found. No changes made.")


def setup(bot):
    Tasks(bot)
