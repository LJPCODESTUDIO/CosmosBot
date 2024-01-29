import os
import glob
import disnake
import random
import json
import time
import threading
from pytube import YouTube, Search
from requests import get
from disnake.ext import commands
from pyradios import RadioBrowser

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = {}
        self.current_song = {}
        self.loop_queue = {}
        self.loop = {}
        self.radio = {}
        self.radio_queue = {}
        self.mode = {}
        self.thread = threading.Thread(target=self.delete_songs())

        self.setup()
    
    # Delete all the locally saved songs it can
    def delete_songs(self):
        songs = glob.glob("./Local/Audio_Files/*")

        print("Checking songs...")
        for song in songs:
            can_delete = True
            for guild in self.current_song:
                for info in self.current_song[guild]:
                    if os.path.basename(song) in info:
                        can_delete = False
            
            for guild in self.song_queue:
                for info in self.song_queue[guild]:
                    if os.path.basename(song) in info:
                        can_delete = False
            
            if can_delete:
                print(f"Deleting: {song}")
                try:
                    os.remove(song)
                except:
                    print(f"Couldn't delete: {song}")

    # Simple setup function to run at init
    def setup(self):
        with open("radio.json") as f:
            radio_file = json.load(f)
        old_audio = glob.glob("./Local/Audio_Files/*")

        for f in old_audio:
            os.remove(f)

        for guild in self.bot.guilds:
            self.song_queue[guild.id] = []
            self.loop_queue[guild.id] = False
            self.loop[guild.id] = False
            self.current_song[guild.id] = []
            self.radio_queue[guild.id] = radio_file
            self.mode[guild.id] = 0
    
    # Downloads a given URL and returns a constructed song info list
    def download_song(self, _url):
        stream = YouTube(url=_url).streams.filter(only_audio=True).first()
        filepath = f"./Local/Audio_Files/{stream.default_filename}"

        stream.download("./Local/Audio_Files")

        return [stream.default_filename, _url, filepath]

    # Simply put, plays the corrosponding audio file
    def play_song(self, ctx, song, old_song=None):
        self.current_song[ctx.guild.id] = song
        ctx.voice_client.play(disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(song[2]), 0.5), after=lambda error: self.check_queue(ctx))
        self.delete_songs()

    # To run after every song. Checks the queue to see if there is another song to play
    def check_queue(self, ctx):
        if self.loop[ctx.guild.id]:
            return self.play_song(ctx, self.current_song[ctx.guild.id])
        
        if self.loop_queue[ctx.guild.id]:
            self.song_queue[ctx.guild.id].append(self.current_song[ctx.guild.id])

        old_song = self.current_song[ctx.guild.id]
        self.current_song[ctx.guild.id] = []

        if self.song_queue[ctx.guild.id] == []:
            return
        
        next_song = self.song_queue[ctx.guild.id].pop(0)

        self.play_song(ctx, next_song, old_song)

    # Joins the authors VC
    @commands.command(aliases=["j"], help="Joins your current VC")
    async def join(self, ctx):
        self.delete_songs()
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC")
        
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        
        await ctx.author.voice.channel.connect()
        print(f"Joined channel: {str(ctx.voice_client.channel)}")
    
    # Leaves the current VC
    @commands.command(help="Leaves the current VC")
    async def leave(self, ctx):
        self.delete_songs()
        if ctx.voice_client is None:
            return await ctx.send("I can't leave a VC when I'm not in one")
        
        print(f"Left channel: {str(ctx.voice_client.channel)}")
        await ctx.voice_client.disconnect()

    # Searches for and plays a song, or adds it to the queue
    @commands.command(aliases=["p"], help="Play a song from youtube or a download")
    async def play(self, ctx, searchterm):
        attachments = ctx.message.attachments
        if ctx.author.voice is None:
            return await ctx.send("I can't join you if your not in a VC")

        if searchterm is None and attachments == []:
            return await ctx.send("I can't play nothing, please include a song")
        
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
            print(f"Joined channel: {str(ctx.voice_client.channel)}")

        # TODO if an attachment is included, just use that
        if attachments != []:
            pass

        # Check if the searchterm is a url. If it isn't, search for the term
        if "youtube.com/watch?" in searchterm or "https://youtu.be/" in searchterm:
            songurl = searchterm
        else:
            print(f"Searching for song: {searchterm}")
            await ctx.send("Searching for the song...")
            songurl = Search(searchterm).results[0].watch_url
        
        print(f"Downloading: {songurl}")
        await ctx.send("Downloading song...")
        song_info = self.download_song(songurl)

        # Check if a song is playing or not, if one is, add this one to the queue
        if self.current_song[ctx.guild.id] == []:
            print(f"Playing song: {song_info[1]}")
            await ctx.send(f"Playing song: {song_info[1]}")
            self.play_song(ctx, song_info)
        else:
            queue_len = len(self.song_queue[ctx.guild.id])

            if queue_len < 25:
                print(f"Adding song to queue")
                self.song_queue[ctx.guild.id].append(song_info)
                await ctx.send(f"Currently playing a song. Song added to queue at position: {queue_len + 1}")
            else:
                await ctx.send("Maximum queue length of 25 reached. Please wait for this song to finish then try again")
    
    # Enables/disables loop
    @commands.command(aliases=["l"], help="Loops the current song. Takes precedence")
    async def loop(self, ctx):
        self.delete_songs()
        if self.loop[ctx.guild.id]:
            self.loop[ctx.guild.id] = False
            return await ctx.send("Loop disabled")
        
        self.loop[ctx.guild.id] = True
        await ctx.send("Loop enabled")
    
    # Enables/disables loop_queue
    @commands.command(aliases=["lq"], help="Loops the playlist")
    async def loop_queue(self, ctx):
        self.delete_songs()
        if self.loop_queue[ctx.guild.id]:
            self.loop_queue[ctx.guild.id] = False
            return await ctx.send("Loop queue disabled")
        
        self.loop_queue[ctx.guild.id] = True
        await ctx.send("Loop queue enabled")
    
    # Command to skip the current song
    @commands.command(aliases=['s'], help='Skips the current song.')
    async def skip(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I'm not playing anything. I can't skip nothing.")
        
        if ctx.author.voice is None:
            return await ctx.send("You aren't in a VC, so I'm going to ignore you.")
        
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("We aren't in the same VC, don't skip other peoples music!")
        
        ctx.voice_client.stop()
    
    # Display the current queue
    @commands.command(aliases=["q"], help="Displays the current song queue")
    async def queue(self, ctx):
        self.delete_songs()
        if len(self.song_queue[ctx.guild.id]) == 0:
            return await ctx.send("There are no songs in the queue")
        
        embed = disnake.Embed(title="Song Queue", colour=disnake.Colour.green())
        i = 0
        for info in self.song_queue[ctx.guild.id]:
            i += 1
            embed.add_field(name=f"{i}. {info[0]}", value=info[1], inline=False)

        embed.set_footer(text=f"There are {i}vsongs in the queue")

        await ctx.send(embed=embed)
    
    # Clears the queue
    @commands.command(aliases=['cl'], help='Clears the current queue')
    async def clear(self, ctx):
        if ctx.voice_client is None:
            return await ctx.send("I'm not playing anything.")
        
        if ctx.author.voice is None:
            return await ctx.send("You aren't in a VC, so I'm going to ignore you.")
        
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("We aren't in the same VC, don't clear other peoples queue!")

        self.song_queue[ctx.guild.id].clear()
        self.delete_songs()
        await ctx.send("Queue cleared!")

    # Removes a song from the queue
    @commands.command(aliases=['r'], help='Removes a song from the queue based on its position')
    async def remove(self, ctx, pos : int):
        if ctx.voice_client is None:
            return await ctx.send("I'm not playing anything.")
        
        if ctx.author.voice is None:
            return await ctx.send("You aren't in a VC, so I'm going to ignore you.")
        
        if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
            return await ctx.send("We aren't in the same VC, don't clear other peoples queue!")

        info = self.song_queue[ctx.guild.id].pop(pos - 1)
        self.delete_songs()

        await ctx.send(f"Removed song at position: {pos}")

    # Displays the currently playing song
    @commands.command(help="Displays the currently playing song")
    async def np(self, ctx):
        if ctx.voice_client is not None:
            embed = disnake.Embed(title=self.current_song[ctx.guild.id][0], url=self.current_song[ctx.guild.id][1])
            return await ctx.send("Currently playing:", embed=embed)

        await ctx.send("I'm not playing anything.")