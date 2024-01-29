import os
import disnake
import json
import random
from web import web_start
from disnake.ext import commands
from dotenv import load_dotenv
#from music import Music
from music_rewrite import Music
from AIOC import OC, AI

load_dotenv()
TOKEN = os.getenv('TOKEN2')
help_command = commands.DefaultHelpCommand(
    no_category = 'Misc'
)
bot = commands.Bot(
    command_prefix='?',
    intents=disnake.Intents.all(),
    activity = disnake.Activity(type=disnake.ActivityType.watching, name="you from the window"),
    help_command=help_command
)


@bot.event
async def on_ready():
    print('The bot is ready!')


@bot.command(help='Sends a picture of a sandwich.')
async def sandwich(ctx):
    response = ["I don't wanna", "NO!", "Go make one yourself", "I shall not", "How about, no"]
    make = random.randint(0, 1)
    if make == 1:
        await ctx.send(file=disnake.File('sandwich.jpg'))
    else:
        pick_response = random.randint(0, 4)
        await ctx.send(response[pick_response])


async def setup():
    await bot.wait_until_ready()
    #open and store json file as python
    with open('servers.json') as f:
        guilds = json.load(f)
    #edit json
    for guild in bot.guilds: 
        if str(guild.id) not in guilds['servers']:
            with open('characters.json') as f:
                char = json.load(f)
            char['servers'].update({str(guild.id):[]})
            guilds['servers'].update({str(guild.id):guild.name})
            with open('characters.json', 'w') as f:
                json.dump(char, f, indent=2, sort_keys=True)
            
    #dump back to file
    with open('servers.json', 'w') as f:
        json.dump(guilds, f, indent=2)
    bot.add_cog(Music(bot))
    bot.add_cog(OC(bot))
    bot.add_cog(AI(bot))


if __name__ == '__main__':
    bot.loop.create_task(setup())
    #web_start()
    bot.run(TOKEN)