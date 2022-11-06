from naff import (
    Extension,
    listen,
    slash_command,
    InteractionContext,
    Permissions,
    Embed,
)
from naff.models.discord import color
import json


class Config(Extension):
    print("Config extension loaded")
    # * This command will make a config if it doesn't exist, and allow editing of an existing config
    @slash_command(
        name="config",
        description="View and Change this guild's config",
        sub_cmd_name="view",
        sub_cmd_description="View your guild's current config",
        dm_permission=False,
        default_member_permissions=Permissions.ADMINISTRATOR | Permissions.MANAGE_GUILD,
    )
    async def config_view(self, ctx: InteractionContext):
        # * Get the config from the config.json file
        config = json.load(open("config.json", "r+"))
        # * get this guild's config options
        try:
            guild_config = config["guilds"][str(ctx.guild.id)]
        except KeyError:  # ! guild doesn't have a config set yet, let's make one
            new_config = {
                ctx.guild.id: {
                    "github": False,
                    "dehoisting": False,
                    "mod_log_enabled": False,
                    "mod_log_channel": None,
                    "welcome_channel": None,
                    "welcome": None,
                    "welcome_dm_message": None,
                    "leave_channel": None,
                    "leave": None,
                }
            }
            config["guilds"].update(new_config)
            json.dump(config, open("config.json", "w"), indent=4)
            config = json.load(open("config.json", "r+"))
            guild_config = config["guilds"][str(ctx.guild.id)]
            pass
        on_emoji = "<a:on:957172382827708456>"
        off_emoji = "<a:off:957172308777254912>"
        embed = Embed(
            title=f"{ctx.guild.name} Config",
            description="View and change your guild's config",
            color=color.FlatUIColors.CARROT,
            thumbnail=f"{ctx.guild.icon.url if ctx.guild.icon.url else 'https://cdn.discordapp.com/attachments/943106707381444678/1038755616883212358/unknown.png'}"
        )
        embed.add_field(
            name=f"{on_emoji if guild_config['dehoisting'] else off_emoji} || Member Dehoisting",
            value=f"Dehoist users by adding invisible characters to the front of their name",
            inline=True,
        )
        embed.add_field(
            name=f"{on_emoji if guild_config['github'] else off_emoji} || GitHub Embeds",
            value=f"Embed GitHub links in chat",
            inline=True,
        )
        embed.add_field(
            name=f"{on_emoji if guild_config['mod_log_enabled'] else off_emoji} || Mod Log",
            value=f"Log moderation actions to a channel\nChannel:\n<#{str(guild_config['mod_log_channel'])}>",
            inline=True,
        )
        await ctx.send(embeds=embed)


def setup(bot):
    Config(bot)
