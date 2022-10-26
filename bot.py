import artery_gear_artifact_rater as rater
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = 'NTc1MzI1NDEwOTIxODA3ODcy.GW4gD2.-ARTBIEGp_iGVc7snxjfosvYRoXtCzjq1NnQRg'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='-',intents=intents)

calls = 0

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to {[guild.name for guild in bot.guilds]}')

opt_to_key = {'hp': 'HP', 'atk': 'ATK', 'atk%': 'ATK%', 'resist': 'Status RES%','acc':'Status ACC%',
			  'cr': 'Critical', 'cd': 'CRIT DMG%',
			  'hp%': 'HP%', 'def%': 'DEF%', 'spd': 'SPD', 'def': 'DEF', 'lvl': 'Level'}

@bot.command()
async def test(ctx, arg):
    await ctx.send(arg)

@bot.command(name='rate')
async def rate(ctx):
	'''
	Rate an artifact against an optimal 5* artifact. Put the command and image in the same message.

	-rate <image> [lvl=<level>] [<stat>=<weight> ...]

	Default weights

	ATK%, DMG%, Crit - 1
	ATK, EM, Recharge - 0.5
	Everything else - 0

	Options

	lvl: Compare to specified artifact level (default: 20)
	-rate lvl=0

	<stat>: Set custom weights (valued between 0 and 1)
	-rate atk=1 er=0 atk%=0.5

	<stat> = HP, HP%, ATK, ATK%, ER (Recharge), EM, PHYS, CR (Crit Rate), CD (Crit Damage), ELEM (Elemental DMG%), Heal, DEF, DEF%
	'''
	print('rating')
	if not ctx.message.attachments:
		return
	print('rated')
	options = ctx.message.content.split()[1:]
	options = {opt_to_key[option.split('=')[0].lower()] : float(option.split('=')[1]) for option in options}
	url = ctx.message.attachments[0].url
	suc, text = await rater.ocr(url)
	global calls
	calls += 1
	print(f'Calls: {calls}')
	if suc:
		results = rater.parse(text)
		print(f'results: ', results)
		score, main_score, sub_score = rater.rate(results, options)
		msg = f'Stats: {results}\nGear Score: {score:.2f}% (main {main_score:.2f}%, sub {sub_score:.2f}%)'
	else:
		msg = f'OCR failed. Error: {text}'
		if 'Timed out' in text:
			msg += ', please try again in a few minutes'
	await ctx.send(msg)

bot.run(TOKEN)
