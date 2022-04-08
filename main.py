from compileall import compile_path
import os
import discord
import ffmpeg
import discordSuperUtils
import pysos
import random
import openai
from discordSuperUtils import MusicManager
from discord.ext import commands
from dotenv import load_dotenv

#bot config
bot = commands.Bot(command_prefix='?', activity = discord.Activity(type=discord.ActivityType.watching, name="you from the window"))
bot.remove_command('help')
MusicManager = MusicManager(
    bot, spotify_support=False, inactivity_timeout=None
)

load_dotenv()
db = pysos.Dict('OCList')
TOKEN = os.getenv('TOKEN')
openai.api_key = os.getenv('KEY')
openai.api_base = 'https://api.goose.ai/v1'
# List Engines (Models)
engines = openai.Engine.list()
# Print all engines IDs
for engine in engines.data:
  print(engine.id)

engines = openai.Engine.list()

for engine in engines.data:
    print(engine.id)

@MusicManager.event()
async def on_music_error(ctx, error):
    raise error  # add your error handling here! Errors are listed in the documentation.

@MusicManager.event()
async def on_queue_end(ctx):
    print(f"The queue has ended in {ctx}")
    # You could wait and check activity, etc...

@MusicManager.event()
async def on_inactivity_disconnect(ctx):
    print(f"I have left {ctx} due to inactivity..")

@MusicManager.event()
async def on_play(ctx, player):
    await ctx.send(f"Playing {player}")

@bot.event
async def on_ready():
    print('Bot is ready')

#help command
@bot.command()
async def help(ctx):
    embed=discord.Embed()
    embed.add_field(name="join", value="Has the bot join a voice channel", inline=False)
    embed.add_field(name="leave", value="Has the bot leave the voice channel", inline=False)
    embed.add_field(name="play", value="Searches for and plays a song from youtube", inline=False)
    embed.add_field(name="pause", value="Pauses current song", inline=False)
    embed.add_field(name="resume", value="Resumes current song", inline=False)
    embed.add_field(name="loop", value="Loops the song", inline=False)
    embed.add_field(name="shuffle", value="Shuffles the queue", inline=False)
    embed.add_field(name="queueloop", value="Loops the queue", inline=False)
    embed.add_field(name="skip", value="Skips current song", inline=False)
    embed.add_field(name="np", value="Shows the current song that is playing", inline=False)
    embed.add_field(name="queue", value="Returns the queue", inline=False)
    embed.add_field(name="addOC", value="Adds an OC to the list", inline=False)
    embed.add_field(name="removeOC", value="Removes an OC from the list", inline=False)
    embed.add_field(name="OClist", value="Shows the list", inline=False)
    embed.add_field(name="randomOC", value="Picks a random OC from the list", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def ping(ctx):
  	await ctx.send("pong")

#music commands
@bot.command()
async def leave(ctx):
    if await MusicManager.leave(ctx):
        await ctx.send("Left Voice Channel")


@bot.command()
async def np(ctx):
    if player := await MusicManager.now_playing(ctx):
        duration_played = await MusicManager.get_player_played_duration(ctx, player)
        # You can format it, of course.

        await ctx.send(
            f"Currently playing: {player}, \n"
            f"Duration: {round(duration_played)}/{player.duration}"
        )

@bot.command()
async def play(ctx, *, query: str):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await MusicManager.join(ctx)

    async with ctx.typing():
        players = await MusicManager.create_player(query, ctx.author)

    if players:
        if await MusicManager.queue_add(
            players=players, ctx=ctx
        ) and not await MusicManager.play(ctx):
            await ctx.send("Added to queue")

    else:
        await ctx.send("Query not found.")

@bot.command()
async def pause(ctx):
    if await MusicManager.pause(ctx):
        await ctx.send("Player paused.")

@bot.command()
async def resume(ctx):
    if await MusicManager.resume(ctx):
        await ctx.send("Player resumed.")

@bot.command()
async def loop(ctx):
    is_loop = await MusicManager.loop(ctx)

    if is_loop is not None:
        await ctx.send(f"Looping toggled to {is_loop}")

@bot.command()
async def shuffle(ctx):
    is_shuffle = await MusicManager.shuffle(ctx)

    if is_shuffle is not None:
        await ctx.send(f"Shuffle toggled to {is_shuffle}")

@bot.command()
async def queueloop(ctx):
    is_loop = await MusicManager.queueloop(ctx)

    if is_loop is not None:
        await ctx.send(f"Queue looping toggled to {is_loop}")

@bot.command()
async def skip(ctx, index: int = None):
    await MusicManager.skip(ctx, index)

@bot.command()
async def join(ctx):
    if await MusicManager.join(ctx):
        await ctx.send("Joined Voice Channel")

@bot.command()
async def queue(ctx):
    if ctx_queue := await MusicManager.get_queue(ctx):
        formatted_queue = [
            f"Title: '{x.title}\nRequester: {x.requester and x.requester.mention}"
            for x in ctx_queue.queue[ctx_queue.pos + 1 :]
        ]

        embeds = discordSuperUtils.generate_embeds(
            formatted_queue,
            "Queue",
            f"Now Playing: {await MusicManager.now_playing(ctx)}",
            25,
            string_format="{}",
        )

        page_manager = discordSuperUtils.PageManager(ctx, embeds, public=True)
        await page_manager.run()

@bot.command()
async def addOC(ctx, *, name):
    temp = db['list']
    temp.append(name)
    db['list'] = temp
    print(db['list'])
    await ctx.send('added ' + str(name))
    
@bot.command()
async def removeOC(ctx, *, name):
    temp = db['list']
    try:
    	temp.remove(name)
    	db['list'] = temp
    except:
        await ctx.send('Deletion failed, did you spell it correctly?')
    await ctx.send('removed ' + name)

@bot.command()
async def OClist(ctx):
    embed=discord.Embed()
    embed=discord.Embed(title="OC list", description="List of all the OC's stored on the database")
    print(len(db['list']))
    i = 0
    while i <= len(db['list'])-1:
        print(i)
        x = str(i + 1) + '.'
        embed.add_field(name=x, value=db['list'][i], inline=False)
        i += 1
    await ctx.send(embed=embed)

@bot.command()
async def randomOC(ctx):
    await ctx.send(db['list'][random.randint(0, len(db['list']))])

#AI Writing Commands
@bot.command()
async def prompt(ctx, *, text):
    # Create a completion, return results streaming as they are generated. Run with `python3 -u` to ensure unbuffered output.
    completion = openai.Completion.create(
        engine="gpt-j-6b",
        prompt=text,
        max_tokens=100,
        stream=False)
    await ctx.send(completion)


#@bot.command()
#async def load(ctx, extension):
#    client.load_extension(f'cogs.{extention}')
#    await ctx.send('extension loaded')

#@bot.command()
#async def unload(ctx, extension):
#    client.unload_extension(f'cogs.{extention}')
#    await ctx.send('extension unloaded')

#for filename in os.listdir('./cogs'):
#    if filename.endswith('.py'):
#        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(TOKEN)