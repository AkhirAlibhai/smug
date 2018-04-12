import random
import re
import os

from pyfiglet import Figlet
from discord.ext import commands

import util

class Commands():
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self):
        await self.bot.say('pong!')

    @commands.command()
    async def echo(self, *, message: str):
        ''' echoes a message '''
        await self.bot.say(message)

    @commands.command(pass_context=True)
    async def ninja(self, context, *, message: str):
        ''' Like echo, but deletes the message that issued the command '''
        await self.bot.delete_message(context.message)
        await self.bot.say(message)

    @commands.command()
    async def swapIcon(self):
        '''
        Changes the profile picture randomly. Uses the images found in the
        directory specified in the config file.
        '''
        iconsDirectory = util.config['profile_picture_directory']
        iconsPath = os.path.join(util.basePath, iconsDirectory)
        items = (os.path.join(iconsPath, x) for x in os.listdir(iconsPath))
        files = tuple(x for x in items if os.path.isfile(x))
        with open(random.choice(files), 'rb') as iconFile:
            await self.bot.edit_profile(avatar=iconFile.read())
        await self.bot.say('Profile picture changed!')

    @commands.command()
    async def figlet(self, *, message: str):
        ''' echoes a message with figlet '''
        await self.bot.say(util.markdownCodeBlock(Figlet().renderText(message)))

    @commands.command()
    async def roll(self, *, dice: str='1d6'):
        '''
        Rolls dice using NdN format
        Allows for multiple dice rolls using + as a seperator
        '''
        if (re.fullmatch(util.rollPattern, dice) is None):
            await self.bot.say('Error: Format must be NdN + NdN + NdN + ...')
            return
        diceList = re.split(util.rollSplitPattern, dice)
        results = []
        for d in diceList:
            numRolls, limit = map(int, d.split('d'))
            results.extend(str(random.randint(1, limit + 1)) for x in range(numRolls))
        resultStrings = (str(x) for x in results)
        await self.bot.longSay(', '.join(resultStrings))
        await self.bot.say(f'Total is {sum(int(x) for x in results)}')

    @commands.command(pass_context=True)
    async def userinfo(self, context, *, username: str=None):
        #Prints out info relating to the user that typed this message, or whoever was mentioned in this message
        if username:
            #Checks if there exists a user named 'username'
            user = context.message.server.get_member_named(username)
            if not user:
                #Checks if they mentioned someone
                user = context.message.server.get_member(username)
            if not user:
                #Converts the user to an id
                user = context.message.server.get_member(('\\'+username)[3:-1])
            if not user:
                #Error Message
                await self.bot.say(f'```!userinfo [user]\n\nReturns the '
                                f'userinfo of the person who typed this, '
                                f'or of the user they type.```')
                return
        else:
            user = context.message.author

        #Getting the status of the user
        if user.game:
            game = 'Playing: ' + user.game.name
        else:
            game = 'Status is: '+ (user.status.name).title()

        author = (str(user) +
                (' (Bot)' if user.bot else '') +
                (('/' + str(user.nick)) if user.nick else ''))

        data = discord.Embed(description=game, colour=user.colour)
        data.set_author(name=author)
        data.set_thumbnail(url=user.avatar_url)
        data.add_field(name='User Id', value=user.id, inline=False)
        daysSinceJoined = (user.joined_at.now()-user.joined_at).days
        data.add_field(
            name='Server Join Date',
            value=(f'{user.joined_at.strftime("%B %d, %Y, at %H:%M:%S")}\n'
                   f'({daysSinceJoined} days ago)'),
                   inline=True)
        daysSinceAccountCreated = (user.created_at.now()-user.created_at).days
        data.add_field(
            name='Account Creation Date',
            value=(f'{user.created_at.strftime("%B %d, %Y, at %H:%M:%S")}\n'
                   f'({daysSinceAccountCreated} days ago)'),
                   inline=True)
        roles = ', '.join(role.name for role in user.roles[1:])
        if roles:
            data.add_field(name='Roles', value=roles, inline=False)

        await self.bot.say(embed=data)

def setup(bot):
    bot.add_cog(Commands(bot))
