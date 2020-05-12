#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging
logging.add_colored_handler(logger_name=None, level=logging.DEBUG)
logger = logging.getLogger(__name__)

from os import environ
from typing import List, Union, Type

from flask import Flask
from teleflask import Teleflask
from telemenu.menus import GotoMenu, Menu
from telemenu.machine import TeleMenuMachine
from telestate.contrib.simple import SimpleDictDriver
from pytgbot.api_types.receivable.updates import Update

from telemenu.buttons import ChangeMenuButton, BackButton

__author__ = 'luckydonald'


API_KEY = environ.get('TG_API_KEY')
assert API_KEY  # TG_API_KEY env variable

app = Flask(__name__)
bot = Teleflask(API_KEY, app=app)
menus = TeleMenuMachine(database_driver=SimpleDictDriver(), teleflask_or_tblueprint=bot)


@app.route('/')
def slash():
    logger.debug('aaaa!')
    return "bbbb!"
# end def


@menus.register
class MainMenu(GotoMenu):
    title = "test"
    description = "Lorem ipsum"

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [TestMenu]
    # end def
# end class


@menus.register
class TestMenu(GotoMenu):
    title = "This is a sub menu"
    description = lambda x: f'SUCH WOW {x!r}'

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [BackButton('back')]
    # end def
# end class


@menus.states.ALL.on_command('start')
def cmd_start(update: Update, data: str = None):
    MainMenu.show()
# end def


@bot.on_update
def debug(update: Update):
    logger.info(f'Current state: {menus.states.CURRENT!r}')
    logger.info(f'Current messages listeners: {menus.states.CURRENT.update_handler.message_listeners!r}')
    logger.info(f'Current update listeners: {menus.states.CURRENT.update_handler.update_listeners!r}')
    logger.info(f'Global messages listeners: {menus.states.CURRENT.update_handler.teleflask.message_listeners!r}')
    logger.info(f'Global update listeners: {menus.states.CURRENT.update_handler.teleflask.update_listeners!r}')
# end def
