import io
import json
from datetime import datetime, timedelta
from typing import Mapping, Optional, List, Any

import discord
from discord import Message, Interaction
from discord.ext import commands
from discord.ext.commands import Cog, Command
from discord.ext.commands.context import Context


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

    @client.event
    async def on_message(message: Message):
        if message.author.bot:
            return

        await react_to_mfor_spoiler_logs_if_exists(message)
        await react_to_your_rat_pbs(message)
        await client.process_commands(message)

    async def react_to_mfor_spoiler_logs_if_exists(message: Message):
        if len(message.attachments) > 1:
            return

        for attachment in message.attachments:
            if not attachment.filename.endswith(".json"):
                continue

            spoiler_text = await attachment.read()
            spoiler = json.load(io.BytesIO(spoiler_text))

            embed = discord.Embed()
            embed.colour = discord.Colour.blue()
            embed.title = "MFOR Spoiler File"
            embed.description = f"Generated on {spoiler["MFOR Version"]} with Seed `{spoiler["Seed"]}`"
            field_text = ""
            field_header = f"**Logic Settings**"
            for key, value in spoiler["Settings"].items():
                if key in ["E-Tanks", "Missile Tanks", "Power Bomb Tanks"]:
                    continue

                field_text += f"{key}: {value}\n"
            field_text = field_text.strip()
            embed.add_field(name=field_header, value=field_text)

            gen_button_spoilered = discord.ui.Button(label="Show Item Order (Spoilered)")
            gen_button_revealed = discord.ui.Button(label="Show Item Order (Revealed)")

            async def reply_with_gen_order(interaction: Interaction, spoilered: bool):
                msg = "Item Order:\n"
                spoiler_char = "||" if spoilered else ""
                for index, (key, value) in enumerate(spoiler["Item order"].items()):
                    msg += f"{index}. {spoiler_char}{value} at {key}{spoiler_char}\n"
                msg = msg.strip()
                await interaction.response.send_message(msg)

            async def button_spoilered_callback(interaction: Interaction):
                await reply_with_gen_order(interaction, True)

            async def button_revealed_callback(interaction: Interaction):
                await reply_with_gen_order(interaction, False)

            gen_button_spoilered.callback = button_spoilered_callback
            gen_button_revealed.callback = button_revealed_callback

            view = discord.ui.View()
            view.add_item(gen_button_spoilered)
            view.add_item(gen_button_revealed)

            await message.reply(embed=embed, view=view, mention_author=False)

    async def react_to_your_rat_pbs(message: Message):
        if message.channel.name != "pb-brag":
            return

        if message.content != "YOUR RAT" or len(message.attachments) == 0:
            return

        await message.add_reaction(message.guild.get_emoji(1407560417932214352))  # Your Rat
        await message.channel.send("YOUR RAT")

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
    async def nso(ctx: Context, timestamp_as_str: str):
        """
        for converting NSO runs. Usage is <hour>:<minutes>:<seconds>.<milliseconds> (milliseconds optional)
        """

        if "." not in timestamp_as_str:
            timestamp_as_str += ".0"

        date = datetime.strptime(timestamp_as_str, "%H:%M:%S.%f").time()
        original_delta = timedelta(hours=date.hour, minutes=date.minute, seconds=date.second,
                                   microseconds=date.microsecond)
        multiplier = (60 / 59.7275)
        new_delta = original_delta * multiplier

        def timedelta_to_string(delta: timedelta) -> str:
            days, seconds = delta.days, delta.seconds
            hours = days * 24 + seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60

            # This is convoluted, surely there's a better way?
            # We want to round microseconds. But since those are ints (e.g. 96738), we string-convert them to a float,
            # round them there, string convert them again to get the part past decimal, and then finally convert
            # that as int.
            microseconds = int(str(round(float(f"0.{delta.microseconds}"), 2)).split(".")[1])

            return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{microseconds:<02d}"

        old_time = timedelta_to_string(original_delta)
        new_time = timedelta_to_string(new_delta)

        await ctx.send(f"A {old_time} on Nintendo Switch is equivalent to a {new_time} on original hardware")

    def find_enemy(enemy_name: str) -> tuple[str, dict]:
        with open("enemy_info.json", "r") as f:
            enemy_info = json.load(f)

        for enemy, info in enemy_info.items():
            valid_names = [enemy] + info.get("aliases", [])

            if enemy_name in valid_names:
                return enemy, info

        return "", {}

    def get_all_enemies() -> dict[str, dict]:
        with open("enemy_info.json", "r") as f:
            return json.load(f)

    def find_related_enemies(base_enemy: str) -> list[tuple[str, dict]]:
        parent_name, parent_info = find_enemy(base_enemy)

        if not parent_name:
            return []

        enemies = []
        has_children = "children" in parent_info
        if not has_children:
            # If it doesn't have children defined, check if it has a parent
            for enemy_name, enemy_info in get_all_enemies().items():
                if parent_name not in enemy_info.get("children", []):
                    continue

                parent_name = enemy_name
                parent_info = enemy_info
                break

        enemies.append((parent_name, parent_info))
        for child in parent_info.get("children", []):
            child_name, child_info = find_enemy(child)
            if not child_name:
                raise ValueError(f"Error: Cannot find data for {child}!!!")

            enemies.append((child_name, child_info))

        return enemies

    @client.command()
    async def hp(ctx: Context, *, message=""):
        """
        for the health of an enemy [(list of enemy names)](<https://docs.google.com/spreadsheets/d/1S7UH4Mo8BPfYlp39hxPVUth-IQzjBVaxVK0oC8qWOvA/edit?usp=sharing>)
        """
        enemy_name = message.lower()

        enemies = find_related_enemies(enemy_name)

        message = ""
        for enemy_name, enemy_info in enemies:
            additional_desc = f" {enemy_info["description"]}" if "description" in enemy_info else ""
            message += f"{enemy_name.title()} has {str(enemy_info["health"])} health.{additional_desc}\n"

        await ctx.send(message)

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
