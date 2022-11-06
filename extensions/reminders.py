from naff import Extension
import asyncio
import uuid
from configparser import RawConfigParser
from datetime import datetime, timedelta
from pathlib import Path
import naff.client.errors
import pymongo
from bson import ObjectId
from naff.client.errors import NotFound
from naff.ext.paginators import Paginator
from naff import task
from dpytools.errors import InvalidTimeString
from dpytools.parsers import to_timedelta, Trimmer
from typing import Optional
from naff import (
    slash_command,
    InteractionContext,
    Modal,
    InputText,
    TextStyles,
    Embed,
    Task,
    IntervalTrigger,
    listen,
    ButtonStyles,
)
from naff.models.discord import color
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()
mongoConnectionString = os.getenv("MONGO_CONNECTION_STRING")


def dumb_time(delta: timedelta) -> Optional[str]:
    if delta.total_seconds() <= 0:
        return "<:error:943118535922679879> I'm not sure what you expected, but I can't send reminders in the past"


class Reminders(Extension):
    print("Reminders extension loaded")

    @listen()
    async def on_ready(self):
        self.check_reminders.start()

    @slash_command(
        name="reminders",
        description="Manage your reminders",
        sub_cmd_name="add",
        sub_cmd_description="Add a reminder",
    )
    async def reminder_add(self, ctx: InteractionContext):
        modal = Modal(
            title="Create a reminder",
            components=[
                InputText(
                    label="What do you want to be reminded about?",
                    custom_id="reminder_content",
                    placeholder="Example: set up patreon roles",
                    style=TextStyles.PARAGRAPH,
                    required=True,
                    max_length=3000,
                ),
                InputText(
                    label="When do you want to be reminded?",
                    custom_id="reminder_time",
                    placeholder="Example: 1d 3h to be reminded in 1day and 3hours",
                    style=TextStyles.SHORT,
                    required=True,
                ),
            ],
        )
        await ctx.send_modal(modal)
        client = motor.motor_asyncio.AsyncIOMotorClient(
            mongoConnectionString, serverSelectionTimeoutMS=5000
        )
        db = client.reminders
        # * now we can wait for the modal
        try:
            modal_response = await self.bot.wait_for_modal(modal, timeout=500)
            try:
                time = to_timedelta(modal_response.responses.get("reminder_time"))
            except InvalidTimeString as e:
                await modal_response.send(
                    "<:error:943118535922679879> That doesn't look like a valid time. Please enter the time in the format of <number>[s|m|h|d|w]",
                    ephemeral=True,
                )
                return
            if dumb_time_string := dumb_time(time):
                return await modal_response.send(dumb_time_string)

            what = modal_response.responses.get("reminder_content")
            now = datetime.now()
            when = now + time
            when_timestamp = str(when.timestamp()).split(".")
            when_timestamp = int(when_timestamp[0])
            when_relative = f"<t:{when_timestamp}:R>"
            when_absolute = f"<t:{when_timestamp}:F>"
            if ctx.guild is not None:
                await db.all_reminders.insert_one(
                    {
                        "user_id": ctx.author.id,
                        "channel_id": ctx.channel.id,
                        "time": when_timestamp,
                        "content": what,
                        "done": False,
                        "uuid": str(uuid.uuid4()),
                        "dm": False,
                    }
                )
            else:
                await db.all_reminders.insert_one(
                    {
                        "user_id": ctx.author.id,
                        "time": when_timestamp,
                        "content": what,
                        "done": False,
                        "uuid": str(uuid.uuid4()),
                        "dm": True,
                    }
                )
            embed = Embed(
                title="<a:reminder:956707969318412348> Reminder added",
                color=color.FlatUIColors.CARROT,
                description=f"I'll remind you {when_absolute}({when_relative})\nAbout: {what}",
            )
            await modal_response.send(embeds=embed)
        except asyncio.TimeoutError:  # ! since we have a timeout, we can assume the user closed the modal
            return

    @slash_command(
        name="reminders",
        description="Manage your reminders",
        sub_cmd_name="list",
        sub_cmd_description="List your current reminders",
    )
    async def reminder_list(self, ctx: InteractionContext):
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(
                mongoConnectionString, serverSelectionTimeoutMS=5000
            )
            reminders = client.reminders.all_reminders.find(
                {"user_id": ctx.author.id}
            ).sort("time", pymongo.ASCENDING)
            reminders = await reminders.to_list(None)
            embeds = []
            count = 0
            for reminder in reminders:
                count += 1
                embeds.append(
                    Embed(
                        title=f"<a:reminder:956707969318412348> Reminder {count}",
                        description=f"Content: ```\n{reminder['content']}```\nDue: <t:{reminder['time']}:F>"
                        f"(<t:{reminder['time']}:R>)",
                        color=color.FlatUIColors.CARROT,
                    )
                )
            paginator = Paginator.create_from_embeds(self.bot, *embeds, timeout=300)
            paginator.wrong_user_message = (
                "<:error:943118535922679879> These aren't your reminders"
            )
            paginator.callback_button_emoji = "<:garbagebin:957162939201224744>"
            paginator.show_callback_button = False
            if len(reminders) > 1:
                await paginator.send(ctx)
            elif len(reminders) == 1:
                paginator.show_back_button = False
                paginator.show_first_button = False
                paginator.show_last_button = False
                paginator.show_next_button = False
                await paginator.send(ctx)
            elif len(reminders) == 0:
                embed = Embed(
                    title="<a:reminder:956707969318412348> You have no reminders",
                    color=color.FlatUIColors.CARROT,
                )
                await ctx.send(embeds=embed)

        except BaseException as e:
            embed = Embed(
                title=f"<:error:943118535922679879> Something went wrong",
                description=f"```\n{str(e)}```",
                color=color.FlatUIColors.CARROT,
            )
            await ctx.send(embeds=embed)
            pass

    @Task.create(IntervalTrigger(seconds=5))
    async def check_reminders(self):
        now = str(datetime.now().timestamp()).split(".")
        now = int(now[0])
        client = motor.motor_asyncio.AsyncIOMotorClient(
            mongoConnectionString, serverSelectionTimeoutMS=5000
        )
        db = client.reminders
        reminders = db.all_reminders.find({"done": False}).sort(
            "time", pymongo.ASCENDING
        )
        reminders = await reminders.to_list(length=None)
        for reminder in reminders:
            if now >= reminder["time"]:
                try:
                    if not reminder["dm"]:
                        channel = await self.bot.fetch_channel(reminder["channel_id"])
                    else:
                        channel = await self.bot.fetch_user(reminder["user_id"])
                    await channel.send(f"<@{reminder['user_id']}>,")
                    embed = Embed(
                        title="<a:reminder:956707969318412348> Here's your reminder",
                        color=color.FlatUIColors.CARROT,
                        description=f"You asked me to remind you <t:{reminder['time']}:R>\nAbout: {reminder['content']}",
                    )
                    await channel.send(embeds=embed)
                    await db.all_reminders.delete_one({"uuid": reminder["uuid"]})
                except BaseException:  # ! if channel doesn't exist
                    try:
                        print("Channel not found\nAttempting to DM the user")
                        channel = await self.bot.fetch_user(reminder["user_id"])
                        await channel.send(
                            f"<@{reminder['user_id']}>, I couldn't find or send a message in the original channel you asked in\n"
                            f"so here's a DM \:D"
                        )
                        embed = Embed(
                            title="<a:reminder:956707969318412348> Here's your reminder",
                            color=color.FlatUIColors.CARROT,
                            description=f"You asked me to remind you <t:{reminder['time']}:R>\nAbout: {reminder['content']}",
                        )
                        await channel.send(embeds=embed)
                        await db.all_reminders.delete_one({"uuid": reminder["uuid"]})
                    except BaseException as e:
                        print(e)
                        for guild in self.bot.guilds:
                            try:
                                user = await guild.fetch_member(reminder["user_id"])
                                if user is not None:
                                    await guild.system_channel.send(
                                        f"<@{reminder['user_id']}>, I couldn't find the channel you asked for this in, and your DMs are closed\n"
                                        f"So I've sent this message to a guild you're in"
                                    )
                                    embed = Embed(
                                        title="<a:reminder:956707969318412348> Here's your reminder",
                                        color=color.FlatUIColors.CARROT,
                                        description=f"You asked me to remind you <t:{reminder['time']}:R>\nAbout: {reminder['content']}",
                                    )
                                    await guild.system_channel.send(embeds=embed)
                                    await db.all_reminders.delete_one(
                                        {"uuid": reminder["uuid"]}
                                    )
                            except NotFound:
                                continue
                            except AttributeError:
                                print(
                                    "I'm out of ideas :), I've tried everything to send a reminder but was unable"
                                )
                                await db.all_reminders.delete_one(
                                    {"uuid": reminder["uuid"]}
                                )

                        pass


def setup(bot):
    Reminders(bot)
