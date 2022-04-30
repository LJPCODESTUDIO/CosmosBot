import os
from timeit import repeat
import disnake
import ffmpeg
import disnakeSuperUtils
import pysos
import random
import openai
from pbwrap import Pastebin
from disnakeSuperUtils import MusicManager
from disnake.ext import commands
from dotenv import load_dotenv
#from web import web_start, create_site

print('Starting Bot')

# bot config
load_dotenv()
TOKEN = os.getenv('TOKEN')
bot = commands.Bot(command_prefix='?', activity = disnake.Activity(type=disnake.ActivityType.watching, name="you from the window"))
bot.remove_command('help')
MusicManager = MusicManager(
    bot, spotify_support=False, inactivity_timeout=None
)

#Database config
db = pysos.Dict('DataBase')
#db['guilds'] = []

#Pastebin config
pb = Pastebin(os.getenv('PASTEBIN_KEY'))
pb.authenticate(os.getenv('NAME'), os.getenv('PASS'))

#AI config
openai.api_key = os.getenv('KEY')
openai.api_base = 'https://api.goose.ai/v1'\

# variables for prompts
completed_prompt = ''
temp_prompt = ''
lorebook = {
    'Scientist':'Scientist is a mentally unstable scientist who owns a tech company called Sintech. In order to hide his mental instability he has learnt not to care about anything. Jacob King is his real name, however he does not tell anybody his real name.',
  }

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
    for i in bot.guilds:
        if str(i.name) not in db['guilds']:
            temp = db['guilds']
            temp.append(str(i.name))
            db['guilds'] = temp
            db['list' + str(i.name)] = []
    print('Bot is ready')
    print('loaded on servers' + str(bot.guilds))

#help command
@bot.command()
async def help(ctx):
    embed=disnake.Embed()
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
    embed.add_field(name="prompt", value="Generates a short story with a given prompt", inline=False)
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

        embeds = disnake.generate_embeds(
            formatted_queue,
            "Queue",
            f"Now Playing: {await MusicManager.now_playing(ctx)}",
            25,
            string_format="{}",
        )

        page_manager = disnake.PageManager(ctx, embeds, public=True)
        await page_manager.run()

@bot.command()
async def addOC(ctx, *, name):
    temp = db['list' + str(ctx.guild.name)]
    temp.append(name)
    db['list' + str(ctx.guild.name)] = temp
    print(db['list' + str(ctx.guild.name)])
    await ctx.send('added ' + str(name))
    
@bot.command()
async def removeOC(ctx, *, name):
    temp = db['list' + str(ctx.guild.name)]
    try:
        temp.remove(name)
        db['list' + str(ctx.guild.name)] = temp
        await ctx.send('removed ' + name)
    except:
        await ctx.send('Deletion failed, did you spell it correctly?')

@bot.command()
async def OClist(ctx):
    embed=disnake.Embed()
    embed=disnake.Embed(title="OC list", description="List of all the OC's stored on the database")
    print(len(db['list' + str(ctx.guild.name)]))
    i = 0
    repeat = 25
    while i <= len(db['list' + str(ctx.guild.name)])-1:
        print(i)
        x = str(i + 1) + '.'
        embed.add_field(name=x, value=db['list' + str(ctx.guild.name)][i], inline=False)
        if i == repeat:
            embed=disnake.Embed()
            repeat += 25
        i += 1
    await ctx.send(embed=embed)

@bot.command()
async def randomOC(ctx):
    l_length = len(db['list' + str(ctx.guild.name)])
    if l_length == 0:
        await ctx.send(db['list' + str(ctx.guild.name)][0])
    else:
        await ctx.send(db['list' + str(ctx.guild.name)][random.randint(0, l_length)])

#AI Writing Commands
@bot.command()
async def prompt(ctx, *, text):
    repeat = 0
    # Create a completion, return results streaming as they are generated. Run with `python3 -u` to ensure unbuffered output.
    completed_prompt = ''
    temp_lore = ''''''
    for i in lorebook.keys():
        if i in text:
            if not lorebook[i] in temp_lore:
                temp_lore += lorebook[i]
                temp_lore += '''
                '''
    print(temp_lore)
    temp_prompt = text
    completion = openai.Completion.create(
        engine="gpt-j-6b",
        prompt=temp_lore + text,
        max_tokens=600,
        stream=True)
    await ctx.send('Generating story...')
    for c in completion:
        print (c.choices[0].text, end = '')
        temp_prompt += c.choices[0].text
    completed_prompt += temp_prompt

    while repeat <= 2:
        temp_lore = ''''''
        for i in lorebook.keys():
            if i in completed_prompt:
                if not lorebook[i] in temp_lore:
                    temp_lore += lorebook[i]
                    temp_lore += '''
                    '''
        print(temp_lore)
        completion = openai.Completion.create(
            engine="gpt-j-6b",
            prompt=temp_lore + completed_prompt,
            max_tokens=200,
            stream=True)
        temp_prompt = ''
        for c in completion:
            print (c.choices[0].text, end = '')
            temp_prompt += c.choices[0].text
        completed_prompt += temp_prompt
        repeat += 1
    await ctx.send('Story generated, read it here: ' + pb.create_paste(completed_prompt, 0, 'story' + str(random.randint(1, 100))))
    # await ctx.send('Story generated, read it here: ' + create_site(completed_prompt, str(random.randint(1, 100))))

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
#web_start()
bot.run(TOKEN)