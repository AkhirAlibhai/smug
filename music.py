import re
import os
import discord
import urllib.parse
import urllib3
import util
import asyncio

from discord.ext import commands
from collections import deque
from bs4 import BeautifulSoup

#Song class
class songData:
    def __init__(self, textResults):
        self.url = f"https://www.youtube.com{textResults[0]['href']}"
        self.title = textResults[0]['title']

        #Parsing the duration value
        textResults[1] = str(textResults[1])
        begining = textResults[1].find(":")+2
        middle = textResults[1][begining:].find(":")+begining
        end = textResults[1].find(".</span>")

        self.minutes = textResults[1][begining:middle]
        self.seconds = textResults[1][middle+1:end]

    def printData(self):
        return (f"Title: {self.title}\nUrl: `{self.url}`"
                f"\nDuration: {self.minutes}m{self.seconds}s")


#Declares the voiceClient
global voiceClient
voiceClient = 0

#Declares the player
global player
player = 0

#Declares the musicQueue
global musicQueue
musicQueue = deque()

global musicChannel
musicChannel = deque()

async def join(self, context):
    #Makes the bot join whichever channel the user that typed this command is in
    #Checks if the user is in a voice chanel
    if context.message.author.voice.voice_channel:
        #Setting voiceClient
        global voiceClient
        if voiceClient:
            await self.bot.say(f"I'm already in a voice channel")
        else:
            voiceClient = await self.bot.join_voice_channel(
                                context.message.author.voice.voice_channel)
    else:
        await self.bot.say(f"Please join a voice channel")

async def leave(self, context):
    #Makes the bot leave whichever voice channel it is in
    global voiceClient
    global player
    #Checks if the bot is in a channel
    if voiceClient:
        await voiceClient.disconnect()
        voiceClient = 0
        player = 0
    else:
        await self.bot.say(f"Can't leave a channel if I'm not in one")

async def youtube(self, songName, directCall: bool=True):
    #Searches youtube with the given parameters
    if songName:
        http = urllib3.PoolManager()
        query = urllib.parse.quote(songName)
        url = f'https://www.youtube.com/results?search_query=' + query
        response = http.request('GET', url)
        soup = BeautifulSoup(response.data, "html.parser")

        for video in soup.findAll(attrs={'class':'yt-lockup-title'}):

            textResults = []
            for x in video:
                textResults.append(x)

            #Checks if the video is a url
            if textResults[0]['href'][0:6] == '/watch':
                videoData = songData(textResults)
                break

        if directCall:
            await self.bot.say(videoData.printData())
        return videoData.url
    else:
        await self.bot.say(f"```!youtube [name]\n\nType a video title "
                            f"and the bot will return information on "
                            f"the first result```")

async def play(self, context, songURL):
    #Plays the song typed in
    #Checks if a song was entered
    if songURL:
        global voiceClient
        global player
        global musicQueue
        global musicChannel
        #Checks if the bot is in a voice channel, if not, joins the channel
        if voiceClient == 0:
            await join(self, context)

        #Checks if a url was passed in, or not
        if songURL[:4] != "http":
            songURL = await youtube(self, songURL, False)

        #Checks if something is already playing
        if player:
            #If yes, queues the song
            #Creates the player
            queuePlayer = await voiceClient.create_ytdl_player(songURL)
            musicQueue.append(queuePlayer)
            musicChannel.append(context.message.channel)
            await self.bot.say(f"Queued **{queuePlayer.title}**")
            return

        #Creates the player
        player = await voiceClient.create_ytdl_player(songURL,
                                                    after = lambda: playNext(self))
        musicChannel.append(context.message.channel)
        await self.bot.say(f"Now playing: **{player.title}**")

        #Plays the song
        player.start()
    else:
        await self.bot.say(f"```!play [url]\n\nType a song url to "
                            f"queue it, or type a name and select whichever "
                            f"you want to play from the list.```")

def playNext(self):
    global player
    global musicQueue
    global musicChannel
    global voiceClient
    #Resetting the player variable
    player = 0
    #Checks if there is something in the queue
    if len(musicQueue) > 0:
        #Gets the next song
        player = musicQueue.popleft()

        #Makes the new player
        newPlayer = voiceClient.create_ytdl_player(player.url,
                                                    after = lambda: playNext(self))
        newPlayerResult = asyncio.run_coroutine_threadsafe(newPlayer, self.bot.loop)

        #Tries to kill the old player, still need to fix this
        player.start()
        player.stop()

        #Starts the next song
        player = newPlayerResult.result()

        #Says that the next song has started in the channel it was queued in
        sayNextSong = self.bot.send_message(musicChannel.popleft(), f"Now Playing **{player.title}**")
        sayNextSongFuture = asyncio.run_coroutine_threadsafe(sayNextSong, self.bot.loop)

        player.start()

class Music():
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def leave(self, context):
        await leave(self, context)

    @commands.command()
    async def youtube(self, *, songName: str=None):
        await youtube(self, songName)

    @commands.command(pass_context=True)
    async def play(self, context, *, songURL: str=None):
        await play(self, context, songURL)

    @commands.command(pass_context=True)
    async def skip(self, context):
        #Checks if the player is playing something
        global player
        if (player != 0):
            player.stop()
            await self.bot.say("Song was skipped")
        else:
            #If nothing is playing
            await self.bot.say("Can't skip if I'm not playing")

    @commands.command()
    async def playing(self):
        #Prints out what song the bot is currently playing
        #Checks if something is playing
        if (player == 0):
            await self.bot.say(f"Nothing is playing")
            return
        #Converts minutes to seconds
        minutes = player.duration//60
        seconds = player.duration%60
        queueInformation = (f"Playing: **{player.title}**\n"
                            f"Duration: {str(minutes)}m{str(seconds)}s.\n"
                            f"<{player.url}>")

        #Checks if the queue is empty
        global musicQueue
        if len(musicQueue) == 0:
            await self.bot.say(queueInformation)
            return

        #To print the contents queue
        queueInformation += (f'\n\nSongs in queue:\n')
        counter = 1
        for song in musicQueue:
            minutes = song.duration//60
            seconds = song.duration%60
            currentSong = (f"\t{str(counter)}) **{song.title}**\n"
                            f"\tDuration: {str(minutes)}m{str(seconds)}s.\n")
            #Since the message character limit is 2000, splits the message into ones within the limit
            if len(queueInformation+currentSong) > 2000:
                await self.bot.say(queueInformation)
                queueInformation = ''
            queueInformation += currentSong
            counter += 1
        await self.bot.say(queueInformation)

    @commands.command(pass_context=True)
    async def devilman(self, context):
        await play(self, context, "https://www.youtube.com/watch?v=diuexInkshA")

def setup(bot):
    bot.add_cog(Music(bot))
