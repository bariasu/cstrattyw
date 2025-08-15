import discord
import random
from enemyinfo import enemyhealth

def runBot(discord_token: str):
	client = discord.Client(intents=discord.Intents.default())

	@client.event
	async def on_ready():
		print({client.user}, 'is live')

	@client.event
	async def on_message(message):
		if message.author == client.user: # checks if the author of the message is the bot; if so, don't reply
			return

		# channel = discord.utils.get(client.get_all_channels(), name='strat-discussion') # set the channel the bot is looking in to '#strat-discussion'
		# if not channel:
		# 	channel = discord.utils.get(client.get_all_channels(), name='strat_discussion') # set the channel the bot is looking in to '#strat_discussion'

		if(message.content.startswith("<@1172249637499981914>")):
			usermessage = message.content
			if(usermessage.startswith("<@1172249637499981914> add")):
				parsed = message.content.split(", ", 4)
				if(len(parsed) != 4 and len(parsed) != 5): # if the parsed array is not 4 or 5 arguments, print the desired format
					await message.channel.send("Proper usage: <@1172249637499981914> add <link>, <strat name>, <location>, <category>, <author> if you want to include an author besides yourself")
				else:
					emoji = '👍'
					await message.add_reaction(emoji)

					channel = discord.utils.get(client.get_all_channels(), name='strats') # sets the channel to the text channel named '#strats'

					# parsing user input
					# @CStrattyW add <link>, <strat name>, <location>, <category>, <author>
						
					if(len(parsed) == 4):
						temp = parsed[0].split() # helper variable to parse the link
						link = temp[2] # video link
						name = parsed[1] # name of strat
						region = parsed[2] # area of game
						category = parsed[3] # category

						await channel.send('[' + name + '](' + link + '), in ' + region + ' for ' + category + ' by ' + message.author.name)
					else:
						temp = parsed[0].split()
						link = temp[2] # helper variable to parse the link
						name = parsed[1] # name of strat
						region = parsed[2] # area of game
						category = parsed[3] # category
						author = parsed[4] # author(s)

						await channel.send('[' + name + '](' + link + '), in ' + region + ' for ' + category + ' by ' + author)

			usermessage = message.content.lower() # making the commands easier to read
			channel = message.channel # setting channel to the channel the message was sent to

			if(usermessage == "<@1172249637499981914> bizhawk"): # posts bizhawk tutorial
				await channel.send("Here's a complete guide for setting up and submitting emulator RTA runs with BizHawk: <https://www.speedrun.com/fusion/forums/sef63>\nHere is a video guide that shows you how to submit valid runs: <https://youtu.be/aG6mWiXZlt8>")
			elif(usermessage == "<@1172249637499981914> tutorial"): # posts fullgame tutorials
				await channel.send("[Any% tutorial](<https://www.youtube.com/playlist?list=PLW3wkDRmBh4jkWezk89bT_rQhb10TxpGk>) by HerculesBenchpress\n[Any% tutorial](<https://www.youtube.com/watch?v=ZIjdl9NZyUI>) by JRP2234\n[Any% tutorial](<https://www.youtube.com/playlist?list=PL3pBMjeS6rYhtLVGWtLoCeD7C2aZrkl9n>) by kirbymastah\n[100% tutorial](<https://youtu.be/OLFBVAf9Kbg>) by HerculesBenchpress")
			elif(usermessage == "<@1172249637499981914> debug"): # posts debug patches
				await channel.send("[English Debug Patch](<https://www.speedrun.com/fusion/resources/sa2pd>)\n[English Skip Loading Fanfare Patch](<https://www.speedrun.com/fusion/resources/g2vyd>)\n[Japanese Debug Patch](<https://www.speedrun.com/fusion/resources/894i6>)\n[Japanese Skip Loading Fanfare Patch](<https://www.speedrun.com/fusion/resources/mbqvq>)")
			elif(usermessage == "<@1172249637499981914> help"): # posts commands
				await channel.send("Available commands:\n- ***add*** <link>, <strat name>, <location>, <category>, <author(s)> to add a strat in <#1172342441349754980>\n- ***bizhawk*** for guides on how to setup BizHawk\n- ***tutorial*** for various full game tutorials\n- ***debug*** for debug patches (useful for practicing)\n- ***nso*** for converting NSO runs\n- ***<enemy name>*** for the health of an enemy [(list of enemy names)](<https://docs.google.com/spreadsheets/d/1S7UH4Mo8BPfYlp39hxPVUth-IQzjBVaxVK0oC8qWOvA/edit?usp=sharing>)\n- ***damage*** for the damage and cooldown value table")
			elif(usermessage == "<@1172249637499981914> nso"): # posts nso converter
				await channel.send("[Converter for NSO runs](<https://nudua.com/convert>) | Enter **60** in \"Source\" and **59.7275** in \"To\"")
			elif((usermessage.split(" ", 1))[1] in enemyhealth): # finds the enemy in the dictionary and returns the health value
				enemyname = (usermessage.split(" ", 1))[1]
				await channel.send(enemyname.title() + " has " + str(enemyhealth.get(enemyname)) + " health")
			elif(usermessage == "<@1172249637499981914> damage"): # posts the damage and cooldown value table
				await channel.send("Damage and cooldown values can be found [here](<https://kb.speeddemosarchive.com/Metroid_Fusion/Game_Mechanics_and_Tricks#Weapon_Information_.5B1.5D>)")
			elif(usermessage == "<@1172249637499981914> yooooooooooo"): # responds to an 11 o yooooooooooo
				await channel.send(message.author.mention + " yooooooooooo")

	client.run(discord_token)
