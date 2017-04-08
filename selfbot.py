import asyncio
import datetime
import discord
import logging
import time
import traceback

from cogs.utils import config
from collections import Counter
from discord.ext import commands

# "Database"
config = config.Config('config.json')

# Logging
log = logging.getLogger('LOG')
log.setLevel(logging.INFO)

fileFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
consoleFormatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%H:%M:%S')

selfFile = logging.FileHandler(filename='Logs/SelfBot' + datetime.datetime.now().strftime("%Y-%m-%d") + '.log', encoding='utf-8', mode='a')
selfFile.setFormatter(fileFormatter)
log.addHandler(selfFile)

selfConsole = logging.StreamHandler()
selfConsole.setFormatter(consoleFormatter)
log.addHandler(selfConsole)

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

discordFile = logging.FileHandler(filename='Logs/Discord' + datetime.datetime.now().strftime("%Y-%m-%d") + '.log', encoding='utf-8', mode='a')
discordFile.setFormatter(fileFormatter)
logger.addHandler(discordFile)

discordConsole = logging.StreamHandler()
discordConsole.setLevel(logging.ERROR)
discordConsole.setFormatter(consoleFormatter)
logger.addHandler(discordConsole)

extensions = ['cogs.cmds',
              'cogs.cogs',
              'cogs.debug',
              'cogs.google',
              'cogs.info',
              'cogs.log',
              'cogs.mal',
              'cogs.misc',
              'cogs.msg',
              'cogs.tools'
              ]

bot = commands.Bot(command_prefix=config.get('prefix', []), description='''Selfbot''', self_bot=True)


# Startup
@bot.event
async def on_ready():
    log.info('------')
    log.info('Logged in as')
    log.info(str(bot.user) + '(' + str(bot.user.id) + ')')
    log.info('------')
    bot.uptime = datetime.datetime.utcnow()
    bot.message_count = 0
    bot.commands_triggered = Counter()
    bot.socket_stats = Counter()
    bot.icount = 0
    bot.mention_count = 0
    bot.mention_count_name = 0
    bot.refresh_time = time.time()
    bot.gamename = config.get('gamestatus', [])
    if config.get('restart', []) == 'true':
        await bot.get_channel(config.get('restart_channel', [])).send(':wave: Back Running!', delete_after=2)
        await config.put('restart', 'false')
        await config.put('restart_channel', [])


# Command Errors
@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await ctx.message.delete()
        await ctx.send('\N{HEAVY EXCLAMATION MARK SYMBOL} Only usable on Servers', delete_after=3)
    elif isinstance(error, commands.CommandInvokeError):
        log.error('In {0.command.qualified_name}:\n{1}'.format(ctx, ''.join(traceback.format_list(traceback.extract_tb(error.original.__traceback__)))))
        log.error('{0.__class__.__name__}: {0}'.format(error.original))


# Increase use count and log to logger
@bot.event
async def on_command(ctx):
    bot.commands_triggered[ctx.command.qualified_name] += 1
    message = ctx.message
    if isinstance(message.channel, discord.DMChannel):
        destination = 'DM with {0.channel.recipient}'.format(message)
    else:
        destination = '#{0.channel.name},({0.guild.name})'.format(message)
    log.info('In {1}:{0.content}'.format(message, destination))


@bot.event
async def on_socket_response(msg):
    if bot.is_ready():
        bot.socket_stats[msg.get('t')] += 1


# Gamestatus
async def status(bot):
    gamename = ''
    while not bot.is_closed():
        if bot.is_ready():
            if bot.gamename:
                if bot.gamename != gamename:
                    log.info('Game changed to playing {}'.format(bot.gamename))
                    gamename = bot.gamename
                await bot.change_presence(game=discord.Game(name=bot.gamename), status=discord.Status.invisible, afk=True)
            else:
                if bot.gamename != gamename:
                    log.info('Removed Game Status')
                    gamename = bot.gamename
                await bot.change_presence(status=discord.Status.invisible, afk=True)
        await asyncio.sleep(20)

# Load Extensions / Logger / Runbot
if __name__ == '__main__':
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            log.warning('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
    bot.loop.create_task(status(bot))
    bot.run(config.get('token', []), bot=False)
