import io
import json
from datetime import datetime, timedelta
from typing import Mapping, Optional, List, Any

import discord
import mars_patcher.constants.game_data as mars_game_data
from discord import Message, Interaction, User, RawReactionActionEvent, PartialEmoji
from discord.ext import commands
from discord.ext.commands import Cog, Command
from discord.ext.commands.context import Context
from mars_patcher.connections import SHORTCUT_LEFT_DOORS, SHORTCUT_RIGHT_DOORS
from mars_patcher.constants.main_hub_numbers import MAIN_HUB_ELE_DOORS
from mars_patcher.patching import BpsDecoder
from mars_patcher.rom import Rom


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
    intents.reactions = True
    intents.members = True

    client = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents,
                          help_command=CustomHelpCommand())

    @client.event
    async def on_ready():
        print({client.user}, 'is live')

    @client.event
    async def on_raw_reaction_add(payload: RawReactionActionEvent):
        user = await client.fetch_user(payload.user_id)

        if user.bot:
            return

        message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)

        await act_with_role_on_react(payload.emoji, user, message, False)

    @client.event
    async def on_raw_reaction_remove(payload: RawReactionActionEvent):
        user = await client.fetch_user(payload.user_id)

        if user.bot:
            return

        message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)

        await act_with_role_on_react(payload.emoji, user, message, True)

    @client.event
    async def on_message(message: Message):
        if message.author.bot:
            return

        await react_to_mfor_spoiler_logs_if_exists(message)
        await react_to_mfor_bps_file_if_exists(message)
        await react_to_your_rat_pbs(message)

        await client.process_commands(message)

    async def act_with_role_on_react(reaction: PartialEmoji, user: User, message: Message, remove: bool):
        if message.id != 1411451852003868913:  # roles channel
            return

        with open("role_reaction_mappings.json", "r") as f:
            role_reaction_mappings = json.load(f)

        message_id_str = str(message.id)
        if str(message_id_str) not in role_reaction_mappings:
            return

        role_str = role_reaction_mappings[message_id_str].get(str(reaction))
        if not role_str:
            return

        role = await message.guild.fetch_role(role_str)
        member = await message.guild.fetch_member(user.id)

        if remove:
            await member.remove_roles(role)
        else:
            await member.add_roles(role)

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

    async def react_to_mfor_bps_file_if_exists(message: Message):
        if len(message.attachments) > 1:
            return

        for attachment in message.attachments:
            if not attachment.filename.endswith(".bps"):
                continue

            rom = Rom("metroid4.gba")

            with open("metroid4.gba", "rb") as f:
                rom.data = BpsDecoder().apply_patch(await attachment.read(), f.read())

                if rom.read_ascii(7657860, 9) != "RED DOORS":
                    # Not mfor
                    return

            # Prepare offsets and data
            hidden_data_offset = 3926048
            security_offset = 479192
            pb_offsets = (24756, 24756)
            sax_offset = 395796
            box_offset = 8326096
            varia_core_offset = 8326260
            missile_data_offsets = (24828, sax_offset + 1, 465582, box_offset + 13, box_offset + 21, box_offset + 29,
                                    varia_core_offset + 13, varia_core_offset + 21, varia_core_offset + 29)

            source_area = 0
            start_address = mars_game_data.area_connections(rom)
            area_connections = {}
            while source_area != 255:
                source_area = rom.read_8(start_address)
                source_door = rom.read_8(start_address + 1)
                target_area = rom.read_8(start_address + 2)
                start_address += 3
                area_connections[f"{source_area}-{source_door}"] = target_area

            major_locations = [
                # Bosses
                "Arachnus",
                "Yakuza",
                "Ridley",
                "Charge Core-X",
                "Zazabi",
                "Nettori",
                "Wide Core-X",
                "Serris",
                "Nightmare",
                "Mega Core-X",
                "BOX-2",
                # Data
                "Main Deck : Data Room",
                'Sector 2 : Data Room',
                'Sector 3 : Data Room',
                'Sector 4 : Data Room',
                'Sector 5 : Data Room',
                # E-tank
                "Arachnus Room",
                "Reactor Silo Hallway",
                "Arachnus Alcove",
                "Sector 1: Entry Hallway",
                "Ridley Area E-Tank",
                'Sector 1: Speed Ceiling',
                "Sector 2: Zazabi Access",
                "Sector 2: Nettori Owtches",
                "Crumble City Upper Item",
                "Sector 3: Sidehopper Hallway",
                "Sector 3: Upper Nova Stairway",
                "Sector 3: Shinespark Puzzle",
                "Sector 4: Collapsed Ceiling",
                "Sector 4: Crab Battle",
                "Sector 5: E-Tank Mimic",
                "Sector 5: Minifridge",
                "Sector 5: Nightmare Drop",
                "Sector 6: Power Bomb Wall",
                "Sector 6: Bomb Chain Alcove",
                "Sector 6: Pillar Highway",
                # Security room
                "Sector 2 : Security Room",
                "Sector 3 : Security Room",
                "Sector 5 : Security Room",
                "Sector 4 : Security Room",
            ]
            major_offsets = {
                'ChargeBeam': 7655617,
                'WideBeam': 7655725,
                'PlasmaBeam': 7655833,
                'WaveBeam': 7655941,
                'IceBeam': 7656049,
                'MainMissiles': 7656157,
                'SuperMissileItem': 7656265,
                'IceMissileItem': 7656373,
                'DiffusionItem': 7656481,
                'Bombs': 7656589,
                'MainPowerBombs': 7656697,
                'MorphBall': 7656805,
                'HiJumpBoots': 7656913,
                'SpeedBooster': 7657021,
                'SpaceJump': 7657129,
                'ScrewAttack': 7657237,
                'VariaSuit': 7657345,
                'GravitySuit': 7657453,
                'GreenDoors': 7657561,
                'BlueDoors': 7657669,
                'YellowDoors': 7657777,
                'RedDoors': 7657885,
            }

            hidden_items = rom.read_bytes(hidden_data_offset, 24) == b"L\x00M\x00N\x00O\x00" * 3

            is_major_minor_split = True
            for major, offset in major_offsets.items():
                last_read = b"\xFF"
                chars = 0
                while last_read != 0:
                    last_read = rom.read_8(offset + chars)
                    chars += 1
                location = rom.read_ascii(offset, chars - 1).strip()
                if location not in major_locations:
                    is_major_minor_split = False
                    break

            missile_upgrades_give_data = "".join(
                [str(rom.read_8(offset)) for offset in missile_data_offsets]) == "151515248248"
            pb_without_bombs = rom.read_8(pb_offsets[0]) == rom.read_8(pb_offsets[1]) == 32
            split_security = rom.read_16(security_offset) == 0

            vanilla_elevators = True
            for index, room in enumerate(MAIN_HUB_ELE_DOORS, start=1):
                if area_connections[f"0-{room}"] != index:
                    vanilla_elevators = False
                    break

            vanilla_left_tubes = [3, 1, 5, 2, 6, 4]
            vanilla_right_tubes = [2, 4, 1, 6, 3, 5]
            rom_left_tubes = [area_connections[f"{index}-{door}"] for index, door in
                              enumerate(SHORTCUT_LEFT_DOORS, start=1)]
            rom_right_tubes = [area_connections[f"{index}-{door}"] for index, door in
                               enumerate(SHORTCUT_RIGHT_DOORS, start=1)]
            vanilla_tubes = vanilla_left_tubes == rom_left_tubes and vanilla_right_tubes == rom_right_tubes

            first_tileset_offset = 4219100
            first_tileset_length = 8
            first_tileset_data = b'\xe0B@\xff\xb3^%\xa1\xc2\x0b-\xc3\xe0\x03=\x08'
            vanilla_tilesets = b"".join([rom.read_bytes(first_tileset_offset + index * 15, 2) for index in
                                         range(first_tileset_length)]) == first_tileset_data

            first_sprite_offset = 2835304
            first_sprite_length = 8
            first_sprite_data = b'\xc0B\x02\xff\x84\x13+\xed\xeec\x03\xf4\xf2K"\xfb'
            vanilla_sprites = b"".join([rom.read_bytes(first_sprite_offset + index * 15, 2) for index in
                                        range(first_sprite_length)]) == first_sprite_data

            first_suit_offset = 2678268
            first_suit_length = 8
            first_suit_data = b'\x84|S_\xf1G\x7f\x00\xe81S\xef\x00\x00%\x1f'
            vanilla_suits = b"".join([rom.read_bytes(first_suit_offset + index * 15, 2) for index in
                                      range(first_suit_length)]) == first_suit_data

            first_beams_offset = 5813348
            first_beams_length = 9
            first_beams_data = b'\x00\x00\x00\xff\xff\x7f\x7f\xff\xff\x1f\x1f\xfd\xfd\x02\x02??%'
            vanilla_beams = b"".join([rom.read_bytes(first_beams_offset + index, 2) for index in
                                      range(first_beams_length)]) == first_beams_data

            embed = discord.Embed()
            embed.colour = discord.Colour.blue()
            embed.title = "MFOR BPS Patch File"
            filename = attachment.filename.replace("_", " ")
            embed.description = f"File `{filename}`"
            logic_settings_header = f"**Logic Settings**"
            logic_settings_text = (
                f"Item pool: {"Major items anywhere" if not is_major_minor_split else "Limited major item locations"}\n"
                f"Missile upgrades enable Missiles: {missile_upgrades_give_data}\n"
                f"Power Bombs without normal Bombs: {pb_without_bombs}\n"
                f"Separated security levels: {split_security}\n"
                f"Sector shuffle: {not vanilla_elevators}\n"
                f"Tube shuffle: {not vanilla_tubes}\n"
                f"Hide item graphics: {hidden_items}")

            palette_shuffle_header = "**Palette Shuffle**"
            palette_shuffle_text = ""
            if vanilla_tilesets and vanilla_beams and vanilla_suits and vanilla_sprites:
                palette_shuffle_text = "Disabled"
            else:
                palette_shuffle_text = (f"Tileset shuffle: {not vanilla_tilesets}\n"
                                        f"Sprite shuffle: {not vanilla_sprites}\n"
                                        f"Suit shuffle: {not vanilla_suits}\n"
                                        f"Beam shuffle: {not vanilla_beams}")

            logic_settings_text = logic_settings_text.strip()
            palette_shuffle_text = palette_shuffle_text.strip()
            embed.add_field(name=logic_settings_header, value=logic_settings_text)
            embed.add_field(name=palette_shuffle_header, value=palette_shuffle_text)
            await message.reply(embed=embed, mention_author=False)

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
