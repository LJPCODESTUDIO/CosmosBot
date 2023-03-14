from ast import alias
import asyncio
import os
import glob
import disnake
import random
import json
import yt_dlp
from requests import get
from disnake.ext import commands
from pyradios import RadioBrowser


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.current_song = {}
        self.loopqueue = {}
        self.loop = {}
        self.SILENCE = '.\Local\250-milliseconds-of-silence.mp3'
        self.radio_queue = {}
        self.radio = {}
        self.rb = {}
        self.normal = {}
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}

        self.setup()
    
    def setup(self):
        with open('radio.json') as f:
            file = json.load(f)
        files = glob.glob('./Local/Audio_Files/*')
        for f in files:
            os.remove(f)
        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []
            self.loopqueue[guild.id] = False
            self.loop[guild.id] = False
            self.current_song[guild.id] = ''
            self.radio_queue[guild.id] = file
            self.radio[guild.id] = False
            self.rb[guild.id] = False
            self.normal[guild.id] = False

    async def check_queue(self, ctx):
        if ctx.voice_client is None:
            self.current_song[ctx.guild.id] = ''
            self.song_queue[ctx.guild.id] = []
            files = glob.glob('./Local/Audio_Files/*')
            self.normal[ctx.guild.id] = False
            self.radio[ctx.guild.id] = False
            for f in files:
                os.remove(f)
            return
        
        if self.radio[ctx.guild.id] == True:
            with open('radio.json') as f:
                file = json.load(f)
            self.radio_queue[ctx.guild.id] = file
            length = len(self.radio_queue[ctx.guild.id]) - 1
            song = self.radio_queue[ctx.guild.id][random.randint(0, length)]
            return await self.play_song(ctx, song)

        if len(self.song_queue[ctx.guild.id]) > 0:
            #Check if loopqueue is enabled
            #If loopqueue enabled, then add current song to the end of the playlist then play next song
            if self.loopqueue[ctx.guild.id] == True and self.loop[ctx.guild.id] == False:
                self.song_queue[ctx.guild.id].append(self.current_song[ctx.guild.id])
            #Check if loop is enabled, if enabled, play current song
            if self.loop[ctx.guild.id] == True:
                return await self.play_song(ctx, self.current_song[ctx.guild.id])
            #check if current song is local file, then remove it
            if self.current_song.endswith(('.mp3', '.mpeg')) and (self.loopqueue[ctx.guild.id] == False and self.loop[ctx.guild.id] == False) and self.current_song[ctx.guild.id] != '.\Local\250-milliseconds-of-silence.mp3':
                os.remove(f'./Local/Audio_Files/{self.current_song[ctx.guild.id]}')

            await self.play_song(ctx, self.song_queue[ctx.guild.id][0])
            self.song_queue[ctx.guild.id].pop(0)
        else:
            if self.loop[ctx.guild.id] == True:
                return await self.play_song(ctx, self.current_song[ctx.guild.id])
            self.normal[ctx.guild.id] = False
            return await self.play_song(ctx, self.SILENCE)
    
    async def get_song(self, url):
        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            song_info = ydl.extract_info(url, download=False)
        
        return song_info

    async def search_song(self, amount, song, get_url=False):
        with yt_dlp.YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                get(song) 
            except:
                if amount == 1:
                    video = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]
                else:
                    video = ydl.extract_info(f"ytsearch5:{song}", download=False)['entries'][0:amount]
            else:
                video = ydl.extract_info(song, download=False)

        if len(video) == 0:
            return None
        
        if get_url:
            if amount == 1:
                return video["webpage_url"]
            else:
                urls = []
                for url in video:
                    urls.append(url["webpage_url"])
                return urls
        else:
            return video
    
    async def play_song(self, ctx, song):
        #Check if RB is active
        if self.rb[ctx.guild.id] == True:
            source=disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(str(song)))
            ctx.voice_client.play(source, after=None)
            self.current_song[ctx.guild.id] = str(song)
            ctx.voice_client.source.volume = 0.5
            return
        if song.endswith('.mp3' or '.mpeg'):
            #if local song, check if radio is enabled
            if self.radio[ctx.guild.id] == True:
                ctx.voice_client.play(disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(f'./Local/Radio/{song}')), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
            else:
                ctx.voice_client.play(disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(f'./Local/Audio_Files/{song}')), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
            self.current_song[ctx.guild.id] = str(song)
            ctx.voice_client.source.volume = 0.5
            return
        url = await self.get_song(song)
        ctx.voice_client.play(disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(url["url"])), after=lambda error: self.bot.loop.create_task(self.check_queue(ctx)))
        self.current_song[ctx.guild.id] = str(song)
        ctx.voice_client.source.volume = 0.5



    @commands.command(aliases=['j'], help='Joins your current VC.')
    async def join(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC.")
        
        if ctx.voice_client is not None:
            await ctx.author.voice.channel.disconnect()
        
        await ctx.author.voice.channel.connect()
    

    @commands.command(help='Leaves the current VC.')
    async def leave(self, ctx):
        if ctx.voice_client is not None:
            self.normal[ctx.guild.id] = False
            self.radio[ctx.guild.id] = False
            self.rb[ctx.guild.id] = False
            await ctx.voice_client.disconnect()
            return
        
        await ctx.send("I'm not in a voice channel.")


    @commands.command(help='Shows what song is currently playing')
    async def np(self, ctx):
        if ctx.voice_client is not None:
            return await ctx.send(f'Currently playing: {self.current_song[ctx.guild.id]}.')

        await ctx.send("I'm not playing anything.")


    @commands.command(aliases=['pf'], help='Plays an attached audio file. Only supports .mp3 and .mpeg')
    async def play_file(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC.")

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        
        if self.radio[ctx.guild.id] or self.rb[ctx.guild.id] == True:
            return await ctx.send('I cannot play a requested song while the Radio is on.')

        attach = ctx.message.attachments
        #Check if there are any attachments
        if attach == []:
            return await ctx.send('You must include a file.')
        if len(attach) > 1:
            return await ctx.send('Please only include one file.')
        #Check attachments filetype
        for f in attach:
            if f.content_type not in ('audio/mpeg'):
                return await ctx.send('I only support .mp3 files and .mpeg files.')
            #Save attachments to correct location and add the file name to the queue
            try:
                #save the file
                await f.save(f'./Local/Audio_Files/{f.filename}')
                #check if currently playing anything
                if ctx.voice_client.source is not None:
                    queue_len = len(self.song_queue[ctx.guild.id])
                    #If so, add file to queue
                    if queue_len < 25:
                        self.song_queue[ctx.guild.id].append(f.filename)
                        return await ctx.send(f"Currently playing a song, song added to queue at position: {queue_len + 1}.")
                    else:
                        return await ctx.send("Sorry but I a max queue length of 25 songs, please wait for this one to end.")
                #If not, try to play the song
                self.normal[ctx.guild.id] = True
                await self.play_song(ctx, f.filename)
                await ctx.send(f'Playing: {self.current_song[ctx.guild.id]}.')
            except:
                await ctx.send(f"'{f.filename}' failed to save/play.")
    

    @commands.command(aliases=['p'], help='Searches for and plays a song from youtube.')
    async def play(self, ctx, *, song=None):
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC.")

        if song is None:
            return await ctx.send("I can't play nothing, please include a song.")
        
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        if self.radio[ctx.guild.id] or self.rb[ctx.guild.id] == True:
            return await ctx.send('I cannot play a requested song while the Radio is on.')

        # handle song where song isn't url
        if not ("youtube.com/watch?" in song or "https://youtu.be/" in song):
            await ctx.send("Searching for the song, it may take a moment.")

            result = await self.search_song(1, song, get_url=True)

            if result is None:
                return await ctx.send("Sorry I couldn't find the song, try the search command.")
        
        if ctx.voice_client.source is not None:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 25:
                self.song_queue[ctx.guild.id].append(song)
                return await ctx.send(f"Currently playing a song, song added to queue at position: {queue_len + 1}.")
            else:
                return await ctx.send("Sorry but I have a max queue length of 25 songs, please wait for this one to end.")

        self.normal[ctx.guild.id] = True
        await self.play_song(ctx, result)
        await ctx.send(f'Playing: {self.current_song[ctx.guild.id]}.')

    
    @commands.command(aliases=['rs'], help='List the first 5 results from https://www.radio-browser.info')
    async def radio_search(self, ctx, search, *, query=None):
        if query is None:
            return await ctx.send("I could search for nothing but I already know the answer. Please include a search query")

        results = {}

        if search == 'name':
            results = RadioBrowser().search(name=query, limit=5, order='clickcount', hidebroken=True)
        elif search == 'tag':
            results = RadioBrowser().search(tag_list=query, limit=5, order='clickcount', hidebroken=True)
        else:
            return await ctx.send("Please include a search method. Use either 'name', or 'tag'.")
        
        if len(results) == 0:
            return await ctx.send('No results found, please try changing your wording.')

        embed=disnake.Embed(title=f"Results for '{query}':", description='You can use these URLs to play an exact radio.', colour=disnake.Colour.blue())

        for entry in range(0, len(results)):
            name = str((entry + 1)) + '. '  + results[entry]['name']
            url = results[entry]['url']
            homepage = results[entry]['homepage']
            embed.add_field(name=name, value=f'url: {url}\nhomepage: {homepage}', inline=False)
        
        
        amount = len(results)
        embed.set_footer(text=f'Displaying the first {amount} results from https://www.radio-browser.info by clickcount.')
        await ctx.send(embed=embed)


    @commands.command(aliases=['fm'], help='Play/Stop an online radio. Use either a link or a search term.')
    async def radio_fm(self, ctx, *, radio=None):
        if self.rb[ctx.guild.id] == True:
            ctx.voice_client.stop()
            if radio == None:
                self.rb[ctx.guild.id] = False
                await ctx.voice_client.disconnect()
                return await ctx.send('Radio stopped.')
            
        if "youtube.com/watch?" in radio or "https://youtu.be/" in radio:
            return await ctx.send("I unfortunately do not support youtube radios.")
            
        if self.normal[ctx.guild.id] == True:
            return await ctx.send('I cannot play the Radio while there is a requested song to play.')
        
        if self.radio[ctx.guild.id] == True:
            return await ctx.send('I cannot play the Radio while the Radio is playing(Radioception)')
        
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC.")

        if radio is None:
            return await ctx.send("Please include a radio name")

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        
        
        self.rb[ctx.guild.id] = True
        if radio.startswith('http'):
            await self.play_song(ctx, str(radio))
            return await ctx.send(f'Radio link {radio} started.')
        
        link = RadioBrowser().search(name=radio, limit=1, order='clickcount', hidebroken=True)
        if len(link) == 0:
            return await ctx.send('No radio found, consider using ?rs')
        radio_name = link[0]['name']
        await self.play_song(ctx, link[0]['url'])
        return await ctx.send(f'Radio {radio_name} started.')



    @commands.command(help='Plays/Stops the radio.', aliases=['ra'])
    async def radio(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC.")

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        if self.normal[ctx.guild.id] == True:
            return await ctx.send('I cannot play the Radio while there is a requested song to play.')

        if self.rb[ctx.guild.id] == True:
            return await ctx.send('I cannot play the Radio while the Radio is playing(Radioception)')
        
        if self.radio[ctx.guild.id] == True:
            self.radio[ctx.guild.id] = False
            await ctx.voice_client.disconnect()
            return await ctx.send('Radio stopped.')

        self.radio[ctx.guild.id] = True
        length = len(self.radio_queue[ctx.guild.id]) - 1
        song = self.radio_queue[ctx.guild.id][random.randint(0, length)]
        await self.play_song(ctx, song)
        await ctx.send('Radio started.')

    
    @commands.command(help='Displays what songs are in the radio.', aliases=['rq'])
    async def radio_queue(self, ctx):
        with open('radio.json') as f:
                file = json.load(f)
        self.radio_queue[ctx.guild.id] = file
        embed = disnake.Embed(title="Radio Queue", description="", colour=disnake.Colour.dark_gold())
        i = 0
        for url in self.radio_queue[ctx.guild.id]:
            i += 1
            embed.description += f'{i}) {url}\n'
        embed.set_footer(text=f'I am a footer(there are {i} songs in the radio queue.)')
        
        await ctx.send(embed=embed)

    
    @commands.command(help='Loops the queue.', aliases=['lq'])
    async def loopqueue(self, ctx):
        if self.loopqueue[ctx.guild.id] == False:
            self.loopqueue[ctx.guild.id] = True
            return await ctx.send("Loopqueue enabled.")

        self.loopqueue[ctx.guild.id] = False
        await ctx.send("Loopqueue disabled.")

    
    @commands.command(help='Loops the current song, takes priority over LoopQueue', aliases=['l'])
    async def loop(self, ctx):
        if self.loop[ctx.guild.id] == False:
            self.loop[ctx.guild.id] = True
            return await ctx.send("Loop enabled.")

        self.loop[ctx.guild.id] = False
        await ctx.send("Loop disabled.")


    @commands.command(help='Displays the first 5 results of a youtube search.')
    async def search(self, ctx, *, song=None):
        if song is None: return await ctx.send("I could search for nothing but I already know the answer. Please include a search query")

        await ctx.send("Searching for song, this'll take a moment")

        info = await self.search_song(5, song)

        embed = disnake.Embed(title=f"Results for '{song}':", description="*You can use these URL's to play an exact song if the one you want isn't the first result.*\n", colour=disnake.Colour.red())

        amount = 0
        for entry in info["entries"]:
            embed.description += f"\n[{entry['title']}]({entry['webpage_url']})\n"
            amount += 1
        
        embed.set_footer(text=f"Displaying the first {amount} results")
        await ctx.send(embed=embed)


    @commands.command(aliases=['q'], help='Displays the current queue, does not include the current song.')
    async def queue(self, ctx): # display the current queue
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are no songs in the queue.")

        embed = disnake.Embed(title="Song Queue", description="", colour=disnake.Colour.dark_gold())
        i = 0
        for url in self.song_queue[ctx.guild.id]:
            i += 1
            embed.description += f'{i}) {url}\n'
        embed.set_footer(text=f'I am a footer(there are {i} songs in the queue.)')
        
        await ctx.send(embed=embed)


    @commands.command(aliases=['cl'], help='Clears the current queue.')
    async def clear(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I'm not playing anything.")
        
        if ctx.author.voice is None:
            return await ctx.send("You aren't in a VC, so I'm going to ignore you.")
        
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("We aren't in the same VC, don't clear other peoples queue!")

        self.song_queue[ctx.guild.id].clear()
        await ctx.send("Queue cleared!")


    @commands.command(aliases=['r'], help='Removes a song from the queue based on its position.')
    async def remove(self, ctx, pos : int):
        if ctx.voice_client is None:
            return await ctx.send("I'm not playing anything.")
        
        if ctx.author.voice is None:
            return await ctx.send("You aren't in a VC, so I'm going to ignore you.")
        
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("We aren't in the same VC, don't clear other peoples queue!")

        self.song_queue[ctx.guild.id].pop(pos - 1)
        await ctx.send(f"Removed song at position: {pos}")


    @commands.command(aliases=['s'], help='Skips the current song.')
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I'm not playing anything. I can't skip nothing.")
        
        if ctx.author.voice is None:
            return await ctx.send("You aren't in a VC, so I'm going to ignore you.")
        
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("We aren't in the same VC, don't skip other peoples music!")
        
        ctx.voice_client.stop()
        # vote skip code
        '''poll = disnake.Embed(title=f"Vote to Skip Song by - {ctx.author.name}#{ctx.author.discriminator}", description="**80% of the voice channel must vote to skip for it to pass.**", colour=disnake.Colour.blue())
        poll.add_field(name="Skip", value=":white_check_mark:")
        poll.add_field(name="Stay", value=":no_entry_sign:")
        poll.set_footer(text="Voting ends in 15 seconds.")

        poll_msg = await ctx.send(embed=poll) # only returns temporary message, we need to get the cached message to get the reactions
        poll_id = poll_msg.id

        await poll_msg.add_reaction(u"\u2705") # yes
        await poll_msg.add_reaction(u"\U0001F6AB") # no

        await asyncio.sleep(15) #15 seconds to vote

        poll_msg = await ctx.channel.fetcg_message(poll_id)

        votes = {u"\u2705": 0, u"\U0001F6AB": 0}
        reacted = []

        for reaction in poll_msg.reactions:
            if reaction.emoji in [u"\u2705", u"\U0001F6AB"]:
                async for user in reaction.users():
                    if user.voice.channel.id == ctx.voice_client.channel.id and user.id not in reacted and not user.bot:
                        votes[reaction.emoji] += 1

                        reacted.append(user.id)
        
        skip = False
        
        if votes[u"\u2705"] > 0:
            if votes[u"\U0001F6AB"] == 0 or votes[u"\u2705"] / (votes[u"\u2705"] + votes[u"\U0001F6AB"]) > 0.79: # 80% or higher
                skip = True
                embed = disnake.Embed(title="Skip Successful", description="***Voting to skip the current song was succesful, skipping now.***", colour=disnake.Colour.green())

        if not skip:
            embed = disnake.Embed(title="Skip Failed", description="*Voting to skip the current song has failed.*\n\n**Voting failed, the vote requires at least 80% of the members to skip.**", colour=disnake.Colour.red())

        embed.set_footer("Voting ended.")

        await poll_msg.clear_reactions()
        await poll_msg.edit(embed=embed)

        if skip:
            ctx.voice_client.stop()
            await self.check_queue(ctx)'''
    

    @commands.command(help='Pauses the current song.')
    async def pause(self, ctx):
        if ctx.voice_client.is_paused():
            return await ctx.send("I am already paused.")

        ctx.voice_client.pause()
        await ctx.send("The current song has been paused.")


    @commands.command(help='Resumes a paused song.')
    async def resume(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I am not connected to a voice channel.")

        if not ctx.voice_client.is_paused():
            return await ctx.send("I am already playing a song.")
        
        ctx.voice_client.resume()
        await ctx.send("The current song has been resumed.")
