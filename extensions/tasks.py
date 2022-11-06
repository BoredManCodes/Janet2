from naff import Task, IntervalTrigger, Extension, listen
import re


class Tasks(Extension):
    print("Tasks extension loaded")

    # When bot is ready start our tasks
    @listen()
    async def on_ready(self):
        self.dehoist.start()

    # Dehoist users by adding invisible characters to the front of their name
    @Task.create(IntervalTrigger(minutes=1))
    async def dehoist(self):
        for guild in self.bot.guilds:
            await guild.chunk_guild()
            pattern = re.compile("\W")
            count = 0
            print(f"Alright! Scanning and changing nicknames in {guild.name}")
            for x in guild.members:
                if x.display_name[0] == "\u17b5": # Don't re-dehoist users
                    print(f"Skipping {x.display_name}")
                    continue
                if re.sub(pattern, "", x.display_name[0]) == "":
                    print(f"Changing {x.display_name}'s name")
                    try:
                        pnick = x.display_name
                        newnick = "\u17b5" + pnick
                        await x.edit_nickname(
                            new_nickname=newnick,
                            reason=f"Dehoist Command (Ran by timer)",
                        )
                        count += 1
                    except Exception as e:
                        print(e)

            if count != 0:
                print(f"Changed **{count}** nicknames.")
            else:
                print(f"No nicknames found. No changes made.")


def setup(bot):
    Tasks(bot)
