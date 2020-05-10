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


logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

API_KEY = environ.get('API_KEY')
assert API_KEY

app = Flask(__name__)
bot = Teleflask(API_KEY, app=app)
states = TeleStateMachine(__name__, database_driver=SimpleDictDriver(), teleflask_or_tblueprint=bot)
menus = TeleMenuMachine(states)


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


@states.DEFAULT.on_command('start')
def cmd_start(update: Update, data: str = None):
    MainMenu.activate()
    return "Welcome."
# end def
