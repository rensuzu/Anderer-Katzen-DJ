# Duplicate import from bot.py
import os
import sys
import time
import shlex
import shutil
import random
import inspect
import logging
import asyncio
import pathlib
import traceback
import math
import re

import aiohttp
import discord
import colorlog

from io import BytesIO, StringIO
from functools import wraps
from textwrap import dedent
from datetime import timedelta
from collections import defaultdict

from discord.enums import ChannelType
from discord.ext.commands.bot import _get_variable

from . import exceptions
from . import downloader

from .playlist import Playlist
from .player import MusicPlayer
from .entry import StreamPlaylistEntry
from .opus_loader import load_opus_lib
from .config import Config, ConfigDefaults
from .permissions import Permissions, PermissionsDefaults
from .constructs import SkipState, Response, VoiceStateUpdate
from .utils import write_pickle, load_pickle, load_file, write_file, fixg, ftimedelta, _func_

from .constants import VERSION as BOTVERSION    
from .constants import DISCORD_MSG_CHAR_LIMIT, AUDIO_CACHE_PATH

log = logging.getLogger(__name__)

# Extra import that needed in custom command
from subprocess import check_output

# List of custom command
# Should be in a form of method with a start of 'cmd_' + {Command Name}
# This list of method will be bound to bot object, thats why they need self param
  
shows = None
async def cmd_apakah(self, user_mentions, leftover_args):
    """
    Usage:
        {command_prefix}apakah [your query]

    Let kak seto tell his opinion about your question, better prophet than kerang ajaib
    This command will only answer with 'ya' or 'tidak'.
    """
    standardize_user = [user.name for user in user_mentions]

    randomize = random.seed(hash(' '.join(leftover_args + standardize_user)))
    seed = random.random()
    if  seed > 0.5:
        result = 'ya'
    else:
        result = 'tidak'
    return Response(result, reply=True, tts=True)

async def cmd_sleding(self, author, user_mentions):
    """
    Usage:
        {command_prefix}sleding [target...]

    Let kak seto do the sleding, because f*ck your friend
    You should use mention also when executing this command so you won't get sleding-ed
    """
    if user_mentions:
        anak2bgst = [user.mention for user in user_mentions]
        return Response('SAYA SLEDING KEPALA KAMU %s' % ', '.join(anak2bgst), tts=True)
    else:
        return Response('SAYA SLEDING KEPALA KAMU %s' % author.mention, tts=True)

async def cmd_yoi(self, author, leftover_args):
    """
    Usage:
        {command_prefix}yoi [times...]

    Let kak seto tells yoi.
    Set number of times to amplify the memes metre, but please not too many or kak seto will be mad at you
    """
    try:
        times = int(leftover_args[0])
    except:
        return Response('Bgst kamu %s, kasi angka yang bener' % author.mention, tts=True)

    if times < 1:
        return Response('Bgst kamu %s, input harus positif' % author.mention, tts=True)
    elif times > 30:
        return Response('Bgst kamu %s, kebanyakan gblk' % author.mention, tts=True)
    else:
        yoi_str = "yo" * times + "i"
        return Response(yoi_str, tts=True)

async def cmd_please(self, leftover_args):
    """
    Usage:
        {command_prefix}please [your shell command here]
    Ask this bot owner to use this powerfull command
    """
    try:
        extra_char_count = 35
        result = check_output(leftover_args, universal_newlines=True)
        if len(result) > DISCORD_MSG_CHAR_LIMIT - extra_char_count:
            result = result[0:DISCORD_MSG_CHAR_LIMIT - extra_char_count] + "\n..."
    except Exception as e:
        result = "Salah bangsat, {}".format(e)
    return Response(result, codeblock=True, reply=True)
   

async def cmd_git(self, leftover_args):
    """
    Usage:
        {command_prefix}git [git command]
    Pull? Log? Show? As long as it is git
    """
    try:
        extra_char_count = 35
        result = check_output(['git'] + leftover_args, universal_newlines=True)
        if len(result) > DISCORD_MSG_CHAR_LIMIT - extra_char_count:
            result = result[0:DISCORD_MSG_CHAR_LIMIT - extra_char_count] + "\n..."
    except Exception as e:
        result = "Salah euy, {}".format(e)
    return Response(result, codeblock=True, reply=True)


async def cmd_reload_custom(self):
    """
    Usage:
        {command_prefix}reload_custom
    To reload the custom command in bot
    """
    self.load_custom_command(reload=True)
    return Response("Ok. Reloaded", reply=True)

async def cmd_boker(self):
    """
    Usage:
        {command_prefix}boker
    Let kak seto says our boker quote
    """
    return Response("boker cloaker nigger picker", tts=True)
    
async def cmd_grepe(self, author, user_mentions):
    """
    Usage:
        {command_prefix}grepe [target...]

    Show inner dark side of Kak Seto as the on who want to grepe2 someone
    """
    grepe_target = author.mention # Default to author
    if user_mentions:
        anak2bgst = [user.mention for user in user_mentions]
        grepe_target = ', '.join(anak2bgst)    
    return Response('Hai dek %s, saya grepe grepe kamu' % grepe_target, tts=True)

quotes = None

async def cmd_quote(self, leftover_args):
    """
    Usage:
        {command_prefix}quote  => Show a random quotes
        {command_prefix}quote list => List of all available quotes
        {command_prefix}quote add <Your wise quotes> => Add the quotes
        {command_prefix}quote del <n> => Delete n-th quotes from the list
    """
    # Load quotes if this is the first time exec quote

    quotes_file_path = 'data/quotes.txt';
    
    global quotes
    if quotes is None:
        log.debug('Loading the quotes first time')
        quotes = load_file(quotes_file_path)


    if len(leftover_args) > 0:
        # Has param, valid param = list, add, del
        if leftover_args[0] == 'list':
            # Print a list of available quote
            if len(quotes) > 0:
                message = []
                for idx, quote in enumerate(quotes):
                    message.append("[{}]. {}".format(idx, quote))
                return Response('\n'.join(message), codeblock=True)
            else:
                return Response('Empty Quotes', codeblock=True)
        elif leftover_args[0] == 'add':
            # Add a new wise quote
            if len(leftover_args) > 1:
                quotes.append(' '.join(leftover_args[1::]))
                write_file(quotes_file_path, quotes)
                return Response('Thanks. Your qoute has been added', True)
            else:
                # Mising wise quote
                return Response('Please enter a quote', True, tts=True)
        elif leftover_args[0] == 'del':
            # Delete specific index quote
            if len(leftover_args) > 1:
                try:
                    selected_idx = int(leftover_args[1])
                    removed_quotes =  quotes.pop(selected_idx)
                    write_file(quotes_file_path, quotes)
                    return Response("Quotes: `{}` is removed".format(removed_quotes), True, tts=True) 
                except Exception as e:
                    result = "Salah bangsat, {}".format(e)
                    return Response(result, True, tts=True) 
            else:
                # Missing index that need to be deleted
                return Response('Please enter an index', True, tts=True)
    elif len(quotes) > 0:
        # Return random quote
        selected_quote = quotes[random.randint(0, len(quotes)-1)]
        return Response(selected_quote, tts=True)
    else:
        # We dont have any quote yet.
        return Response("Empty Quotes", tts=True)

async def cmd_show(self, leftover_args):
    shows_file_path = 'data/quotes.pkl';
    
    global shows
    if shows is None:
        log.debug('Loading the shows first time')
        try:
            shows = load_pickle(shows_file_path)
        except:
            shows = {}
            write_pickle(shows_file_path, shows)
    if len(leftover_args) > 0:
        if leftover_args[0] == 'list':
            if len(shows) > 0:
                message = []
                for k, v in shows.items():
                    message.append("[{}]. {}".format(k, v))
                return Response('\n'.join(message), codeblock=True)
            else:
                return Response('Empty Shows', codeblock=True)
        elif leftover_args[0] == 'add':
            if len(leftover_args) == 3:
                key = leftover_args[1]
                value = leftover_args[2]
                shows[key] = value
                write_pickle(shows_file_path, shows)
                return Response('Thanks. Your show has been added', True)
            elif len(leftover_args < 3):
                return Response('Please enter key and contents you want to save', True, tts=True)
            elif len(leftover_args > 3):
                return Response('Too many arguments', True, tts=True)
        elif leftover_args[0] == 'del':
            # Delete specific index show
            if len(leftover_args) > 1:
                try:
                    selected_idx = int(leftover_args[1])
                    removed_show =  shows.pop(selected_idx)
                    write_pickle(shows_file_path, shows)
                    return Response("Show: `{}` is removed".format(selected_idx), True, tts=True) 
                except Exception as e:
                    result = "Salah bangsat, {}".format(e)
                    return Response(result, True, tts=True) 
            else:
                return Response('Please enter the key you want to delete', True, tts=True)
        else:
            if len(shows) > 0:
                return Response('Nothing to show', True, tts=True)
            contents = shows.get(leftover_args[0])
            if contents:
                return Response('%s' % contents, True)
            else:
                return Response('Wrong key or command', True, tts=True)