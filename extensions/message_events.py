from naff import Task, IntervalTrigger, Extension, listen, Embed
from naff.api.events import MessageCreate
import re
import json
from naff.models.discord import color
import random

class MessageEvents(Extension):
    print("Message Events extension loaded")
    
    @listen()
    async def on_message_create(self, event = MessageCreate):
        if event.message.author == event.bot.user:  # Don't listen to yourself
            return
        if event.message.guild:
            if ".com/channels" in event.message.content:
                if event.message.guild and event.message.author != event.bot.user:  # Check we aren't in DM's to avoid looping
                    link = event.message.content.split('/')
                    server_id = int(link[4])
                    channel_id = int(link[5])
                    msg_id = int(link[6].split(' ')[0])
                    server = event.bot.get_guild(server_id)
                    channel = server.get_channel(channel_id)
                    quoted = await channel.fetch_message(msg_id)
                    if event.message.guild != quoted.guild:
                        quoted_author = await self.bot.fetch_member(quoted.author.id, quoted.guild.id)
                    else:
                        quoted_author = await self.bot.fetch_member(quoted.author.id, event.message.guild.id)
                    if quoted.attachments:
                        embed = Embed(description=f"{quoted.content}\n\nSent: {quoted.created_at}")
                        embed.set_image(quoted.attachments[0].url)
                    elif quoted.embeds:
                        if quoted.embeds[0].title is not None and quoted.embeds[0].description is not None:
                            embed = Embed(description=f"Embed title: {quoted.embeds[0].title}\n\n{quoted.embeds[0].description}")
                        elif quoted.embeds[0].title is None and quoted.embeds[0].description is not None:
                            embed = Embed(description=f"{quoted.embeds[0].description}")
                        elif quoted.embeds[0].title is not None and quoted.embeds[0].description is None:
                            embed = Embed(description=f"Embed title: {quoted.embeds[0].title}")
                        elif quoted.embeds[0].title and quoted.embeds[0].description is None:
                            return
                    else:
                        embed = Embed(description=f"**{quoted.content}**\n\nSent: {quoted.created_at}")

                    if "#0000" in str(quoted.author): # user is a webhook and will throw a bunch of errors
                        webhook_name = str(quoted.author).split("#")[0]
                        embed.set_author(name=f"{webhook_name} in #{quoted.channel.name}",
                                            url=quoted.jump_url)
                    elif quoted_author is None:
                        embed.set_author(name=f"Deleted User in #{quoted.channel.name}",
                                            url=quoted.jump_url)
                    else:
                        embed.set_author(name=f"{quoted_author.display_name} in #{quoted.channel.name}",
                                            icon_url=quoted_author.display_avatar.url,
                                            url=quoted.jump_url)
                    embed.set_footer(text=f"Quoted by {event.message.author.display_name}", icon_url=event.message.author.avatar._url)
                    embed.color = color.MaterialColors.DEEP_PURPLE
                    if quoted.embeds:
                        try:
                            if quoted.embeds[0].author.name is not None:
                                embed.title = quoted.embeds[0].author.name
                        except AttributeError:
                            pass
                    show_reminder = random.randint(0, 10)
                    if show_reminder == 5:
                        embed.add_field(name="Reminder:", value="You can click the embed's title to view this message's context")

                    await event.message.reply(embed=embed)

                    try:
                        if not quoted.author.bot:
                            if event.message.author != quoted.author: # Don't DM user they quoted themselves
                                try:
                                    if "VIEW_CHANNEL" in str(event.message.channel.permissions_for(quoted_author)):
                                        await quoted.author.send(f"{event.message.author.display_name} mentioned your message\n```\n{quoted.content}```\nin {event.message.channel.mention}!")
                                except RuntimeError:
                                    return
                    except naff.errors.Forbidden:
                        return

            if str(event.bot.user.id) in event.message.content:
                reactions = ["❓"]
                for reaction in reactions:
                    await event.message.add_reaction(reaction)
    
def setup(bot):
    MessageEvents(bot)
