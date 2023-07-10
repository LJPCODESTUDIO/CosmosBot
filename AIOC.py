import disnake
import openai
import json
import random
import os
from dotenv import load_dotenv
from disnake.ext import commands

class OC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(help='Displays the list of Characters added to this servers.')
    async def OClist(self, ctx):
        # open and store JSON file as python
        with open('characters.json') as f:
            char = json.load(f)
        # store the list of the current guild as a new variable
        oclist = char['servers'][str(ctx.guild.id)]
        # print the list as a embed
        embed = disnake.Embed(title="OCList", description="", colour=disnake.Colour.dark_blue())
        i = 0
        for char in oclist:
            i += 1
            embed.description += f'{i}) {char}\n'
        embed.set_footer(text=f'There are {i} characters in this list.')
        await ctx.send(embed=embed)
    
    @commands.command(help='Adds a character to the database using the given name.')
    async def addOC(self, ctx, *, name):
        # open and store JSON file as python
        with open('characters.json') as f:
            char = json.load(f)
        # add the new OC to the python var
        char['servers'][str(ctx.guild.id)].append(str(name))
        char['servers'][str(ctx.guild.id)].sort()
        # dump the python var back to JSON file
        with open('characters.json', 'w') as f:
            json.dump(char, f, indent=2, sort_keys=True)
        await ctx.send(f"Added '{name}' to database.")
    
    @commands.command(help='Removes a character from the database based on their position within.')
    async def removeOC(self, ctx, *, id):
        # open and store JSON file as python var
        with open('characters.json') as f:
            char = json.load(f)
        # remove OC from list based on ID given
        temp = char['servers'][str(ctx.guild.id)].pop(int(id)-1)
        char['servers'][str(ctx.guild.id)].sort()
        # dump the python var back to JSON file
        with open('characters.json', 'w') as f:
            json.dump(char, f, indent=2, sort_keys=True)
        await ctx.send(f"Removed '{temp}' from database.")
    
    @commands.command(help='Selects a random character from this server database.')
    async def randomOC(self, ctx):
        # open and store JSON file as python var
        with open('characters.json') as f:
            char = json.load(f)
        # select a random character from the database
        l_length = len(char['servers'][str(ctx.guild.id)])
        if l_length == 0:
            r_char = char['servers'][str(ctx.guild.id)][0]
            return await ctx.send(r_char)
        r_id = random.randint(0, l_length)
        await ctx.send(char['servers'][str(ctx.guild.id)][r_id])


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        openai.api_key = os.getenv('KEY2')
        openai.api_base = 'https://api.goose.ai/v1'
        # List Engines (Models)
        engines = openai.Engine.list()
        # Print all engines IDs
        for engine in engines.data:
            print(engine.id)
    
    @commands.command(help='Creates an AI generated short story based off of a beginning prompt.\n Available engines are: gpt-neo, gpt-j, cass, fairseq, convo.')
    async def prompt(self, ctx, engine, *, text):
        await ctx.send('Please wait, your story is being generated.')
        if engine == 'gpt-j':
            engine = 'gpt-j-6b'
        elif engine == 'gpt-neo':
            engine = 'gpt-neo-20b'
        elif engine == 'cass':
            engine = 'cassandra-lit-6-9b'
        elif engine == 'fairseq':
            engine = 'fairseq-13b'
        elif engine == 'convo':
            engine = 'convo-6b'
        else:
            return await ctx.send('That is not a valid engine')
        # open JSON file as python var
        with open('stories.json') as f:
            stories = json.load(f)
        # generate prompt
        prompt = openai.Completion.create(
            engine=engine,
            prompt=text,
            max_tokens=500,
            temperature=0.85
        )
        print('\n----------------done----------------\n')
        completed_prompt = text + prompt['choices'][0]['text']
        print(completed_prompt)
        prompt = openai.Completion.create(
            engine=engine,
            prompt=completed_prompt,
            max_tokens=500,
            temperature=0.85
        )
        completed_prompt = completed_prompt + prompt['choices'][0]['text']
        print('\n----------------done----------------\n')
        print(completed_prompt)
        # dump python var back to JSON file
        story_id = str(len(stories) + 1)
        stories.update({story_id:completed_prompt})
        print(stories)
        with open('stories.json', 'w') as f:
            json.dump(stories, f, indent=2)
        # send message with link to generated prompt
        await ctx.send(f'Story generated, read it here: : http://stories.ljpcool.com:10881/{story_id}')