from typing import Mapping, Optional, List, Any

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Command
from discord.ext.commands.context import Context

from enemyinfo import enemyhealth


class CustomHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[Command[Any, ..., Any]]], /) -> None:
        message = "Available commands:\n"
        for cog, commands in mapping.items():
            if not commands:
                continue
            for command in sorted(commands, key=lambda c: c.name):
                if command.hidden:
                    continue
                message += f"- ***{command.name}*** {command.help}\n"

        channel = self.get_destination()
        await channel.send(message)


def run_bot(discord_token: str):
    intents = discord.Intents.default()
    intents.message_content = True

    client = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents,
                          help_command=CustomHelpCommand())

    @client.event
    async def on_ready():
        print({client.user}, 'is live')

    @client.command()
    async def add(ctx: Context, *, message: str):
        """
        <link>, <strat name>, <location>, <category>, <author(s)> to add a strat in <#1172342441349754980>
        """
        # (^ #strats)
        parsed = [s.strip() for s in message.split(",")]
        # If the parsed array is not 4 or 5 arguments, print the desired format
        if len(parsed) < 4 or len(parsed) > 5 or "" in parsed:
            await ctx.send("Proper usage: add <link>, <strat name>, <location>, <category>, <author> "
                           "(if you want to include an author besides yourself)")
            return

        thumbs_up = '👍'
        await ctx.message.add_reaction(thumbs_up)

        strat_channel = discord.utils.get(ctx.guild.channels, name='strats')

        link, name, region, category = parsed[0], parsed[1], parsed[2], parsed[3]
        author = parsed[4] if len(parsed) >= 5 else ctx.author.name

        await strat_channel.send(f"[{name}]({link}), in {region} for {category} by {author}")

    @client.command(ignore_extra=False)
    async def bizhawk(ctx: Context):
        """
        for guides on how to setup BizHawk
        """

        await ctx.send(
            "Here's a complete guide for setting up and submitting emulator RTA runs with BizHawk: <https://www.speedrun.com/fusion/forums/sef63>\n"
            "Here is a video guide that shows you how to submit valid runs: <https://youtu.be/aG6mWiXZlt8>\n")

    @client.command(ignore_extra=False)
    async def tutorial(ctx: Context):
        """
        for various full game tutorials
        """

        await ctx.send(
            "[Any% tutorial](<https://www.youtube.com/playlist?list=PLW3wkDRmBh4jkWezk89bT_rQhb10TxpGk>) by HerculesBenchpress\n"
            "[Any% tutorial](<https://www.youtube.com/watch?v=ZIjdl9NZyUI>) by JRP2234\n"
            "[100% tutorial](<https://youtu.be/OLFBVAf9Kbg>) by HerculesBenchpress\n")

    @client.command(ignore_extra=False)
    async def debug(ctx: Context):
        """
        for debug patches (useful for practicing)
        """

        await ctx.send("[English Debug Patch](<https://www.speedrun.com/fusion/resources/sa2pd>)\n"
                       "[English Skip Loading Fanfare Patch](<https://www.speedrun.com/fusion/resources/g2vyd>)\n"
                       "[Japanese Debug Patch](<https://www.speedrun.com/fusion/resources/894i6>)\n"
                       "[Japanese Skip Loading Fanfare Patch](<https://www.speedrun.com/fusion/resources/mbqvq>)\n")

    @client.command(ignore_extra=False)
    async def nso(ctx: Context):
        """
        for converting NSO runs
        """
        await ctx.send('[Converter for NSO runs](<https://nudua.com/convert>) | '
                       'Enter **60** in "Source" and **59.7275** in "To"')

    @client.command()
    async def enemy(ctx: Context, *, message=""):
        """
        for the health of an enemy [(list of enemy names)](<https://docs.google.com/spreadsheets/d/1S7UH4Mo8BPfYlp39hxPVUth-IQzjBVaxVK0oC8qWOvA/edit?usp=sharing>)
        """
        enemy_name = message.lower().split(" ", 1)[1]
        await ctx.send(f"{enemy_name.title()} has {str(enemyhealth.get(enemy_name))} health")

    @client.command(ignore_extra=False)
    async def damage(ctx: Context):
        """
        for the damage and cooldown value table
        """
        await ctx.send("Damage and cooldown values can be found [here]"
                       "(<https://kb.speeddemosarchive.com/Metroid_Fusion/Game_Mechanics_and_Tricks#Weapon_Information_.5B1.5D>)")

    @client.command(hidden=True, name=f"y{"o" * 11}", ignore_extra=False)
    async def long_yooo_response(ctx: Context):
        # responds to an 11 o yooooooooooo
        await ctx.send(f"{ctx.message.author.mention} y{"o" * 11}")

    client.run(discord_token)
