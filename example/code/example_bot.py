#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from os import environ
from typing import List

from flask import Flask
from teleflask import Teleflask
from telestate import TeleStateMachine
from telemenu.menus import GotoMenu
from telemenu.machine import registerer, TeleMenuMachine
from luckydonaldUtils.logger import logging
from telestate.contrib.simple import SimpleDictDriver
from pytgbot.api_types.receivable.updates import Update

from telemenu.buttons import GotoButton

__author__ = 'luckydonald'

logging.add_colored_handler(logger_name=None, level=logging.DEBUG)
logger = logging.getLogger(__name__)

logging.test_logger_levels()

API_KEY = environ.get('TG_API_KEY')
assert API_KEY  # TG_API_KEY env variable

app = Flask(__name__)
bot = Teleflask(API_KEY, app=app)
menus = TeleMenuMachine(database_driver=SimpleDictDriver(), teleflask_or_tblueprint=bot)


@menus.register
class MainMenu(GotoMenu):
    @classmethod
    def on_inline_query(cls, update: Update):
        pass

    title = "test"
    description = "Lorem ipsum"

    def menus(self) -> List[GotoButton]:
        return []
    # end def
# end class


@menus.states.DEFAULT.on_command('test')
def cmd_test(update: Update, data: str = None):
    return "TEST SUCCESSFUL."
# end def


@bot.on_command('start')
def cmd_start(update: Update, data: str = None):
    MainMenu.show()
    return "Welcome."
# end def


@bot.on_update
def debug(update: Update):
    logger.info(f'Current state: {menus.states.CURRENT!r}')
    logger.info(f'Current messages listeners: {menus.states.CURRENT.update_handler.message_listeners!r}')
    logger.info(f'Current update listeners: {menus.states.CURRENT.update_handler.update_listeners!r}')
    logger.info(f'Global messages listeners: {menus.states.CURRENT.update_handler.teleflask.message_listeners!r}')
    logger.info(f'Global update listeners: {menus.states.CURRENT.update_handler.teleflask.update_listeners!r}')
# end def
