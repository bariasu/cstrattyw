from collections.abc import Callable
from typing import Mapping, Optional, List, Any, Callable, Coroutine

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Command, Context
from discord.ext.commands.context import Context
from discord import Message
import random
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
				message += f"***{command.name}*** {command.help}\n"

		channel = self.get_destination()
		await channel.send(message)


def force_no_arguments(func: Callable[[Context, Any, str], Coroutine]) -> Callable[[Context, Any, str], Coroutine]:
	"""
	Decorator that early exists if the message in a command has any arguments given.
	Note that if you use this, *the command must have its name specified*!.
	"""

	async def wrapper(ctx: Context, *, message: str = "") -> None:
		# Only execute our function if it exists of pure whitespace arguments
		if not message.strip():
			return await func(ctx, message=message)
		return None

	return wrapper


def runBot(discord_token: str):

	intents = discord.Intents.default()
	intents.message_content = True

	client = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents, help_command=CustomHelpCommand())


	@client.event
	async def on_ready():
		print({client.user}, 'is live')

	@client.command()
	async def add(ctx: Context, *, message=""):
		"""
		<link>, <strat name>, <location>, <category>, <author(s)> to add a strat in <#1172342441349754980>
		"""

		parsed = message.split(", ", 4)
		if (len(parsed) != 4 and len(parsed) != 5):  # if the parsed array is not 4 or 5 arguments, print the desired format
			await ctx.send(
				"Proper usage: <@1172249637499981914> add <link>, <strat name>, <location>, <category>, <author> if you want to include an author besides yourself")
		else:
			emoji = '👍'
			await ctx.message.add_reaction(emoji)

			channel = discord.utils.get(client.get_all_channels(),
										name='strats')  # sets the channel to the text channel named '#strats'

			# parsing user input
			# @CStrattyW add <link>, <strat name>, <location>, <category>, <author>

			if (len(parsed) == 4):
				temp = parsed[0].split()  # helper variable to parse the link
				link = temp[2]  # video link
				name = parsed[1]  # name of strat
				region = parsed[2]  # area of game
				category = parsed[3]  # category

				await channel.send(
					'[' + name + '](' + link + '), in ' + region + ' for ' + category + ' by ' + ctx.author.name)
			else:
				temp = parsed[0].split()
				link = temp[2]  # helper variable to parse the link
				name = parsed[1]  # name of strat
				region = parsed[2]  # area of game
				category = parsed[3]  # category
				author = parsed[4]  # author(s)

				await channel.send('[' + name + '](' + link + '), in ' + region + ' for ' + category + ' by ' + author)

	@client.command(name="bizhawk")
	@force_no_arguments
	async def bizhawk(ctx: Context, *, message=""):
		"""
		for guides on how to setup BizHawk
		"""

		await ctx.send("Here's a complete guide for setting up and submitting emulator RTA runs with BizHawk: <https://www.speedrun.com/fusion/forums/sef63>\nHere is a video guide that shows you how to submit valid runs: <https://youtu.be/aG6mWiXZlt8>")

	@client.command(name="tutorial")
	@force_no_arguments
	async def tutorial(ctx: Context, *, message=""):
		"""
		for various full game tutorials
		"""

		await ctx.send("[Any% tutorial](<https://www.youtube.com/playlist?list=PLW3wkDRmBh4jkWezk89bT_rQhb10TxpGk>) by HerculesBenchpress\n[Any% tutorial](<https://www.youtube.com/watch?v=ZIjdl9NZyUI>) by JRP2234\n[Any% tutorial](<https://www.youtube.com/playlist?list=PL3pBMjeS6rYhtLVGWtLoCeD7C2aZrkl9n>) by kirbymastah\n[100% tutorial](<https://youtu.be/OLFBVAf9Kbg>) by HerculesBenchpress")

	@client.command(name="debug")
	@force_no_arguments
	async def debug(ctx: Context, *, message=""):
		"""
		for debug patches (useful for practicing)
		"""

		await ctx.send("[English Debug Patch](<https://www.speedrun.com/fusion/resources/sa2pd>)\n[English Skip Loading Fanfare Patch](<https://www.speedrun.com/fusion/resources/g2vyd>)\n[Japanese Debug Patch](<https://www.speedrun.com/fusion/resources/894i6>)\n[Japanese Skip Loading Fanfare Patch](<https://www.speedrun.com/fusion/resources/mbqvq>)")

	@client.command(name="nso")
	@force_no_arguments
	async def nso(ctx: Context, *, message=""):
		"""
		for converting NSO runs
		"""
		await ctx.send("[Converter for NSO runs](<https://nudua.com/convert>) | Enter **60** in \"Source\" and **59.7275** in \"To\"")

	@client.command()
	async def enemy(ctx: Context, *, message=""):
		"""
		for the health of an enemy [(list of enemy names)](<https://docs.google.com/spreadsheets/d/1S7UH4Mo8BPfYlp39hxPVUth-IQzjBVaxVK0oC8qWOvA/edit?usp=sharing>)
		"""
		enemyname = message.lower().split(" ", 1)[1]
		await ctx.send(enemyname.title() + " has " + str(enemyhealth.get(enemyname)) + " health")

	@client.command(name="damage")
	@force_no_arguments
	async def damage(ctx: Context, *, message=""):
		"""
		for the damage and cooldown value table
		"""
		await ctx.send("Damage and cooldown values can be found [here](<https://kb.speeddemosarchive.com/Metroid_Fusion/Game_Mechanics_and_Tricks#Weapon_Information_.5B1.5D>)")

	@client.command(hidden=True, name="yooooooooooo")
	@force_no_arguments
	async def long_yooo_response(ctx: Context, *, message=""):
		# responds to an 11 o yooooooooooo
		await ctx.send(ctx.message.author.mention + " yooooooooooo")

	client.run(discord_token)
