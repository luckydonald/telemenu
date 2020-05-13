#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

from telemenu.data import Data, MenuData
from telestate import TeleState

logging.add_colored_handler(logger_name=None, level=logging.DEBUG)
logger = logging.getLogger(__name__)

from os import environ
from typing import List, Union, Type

from flask import Flask
from teleflask import Teleflask
from telestate.contrib.simple import SimpleDictDriver

from telemenu.menus import GotoMenu, Menu, RadioMenu, CheckboxMenu
from telemenu.machine import TeleMenuMachine
from telemenu.buttons import ChangeMenuButton, BackButton, GotoButton, RadioButton, CheckboxButton

from pytgbot.api_types.receivable.updates import Update

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
    description = "Lorem ipsum \n\nSUCH DATA\n{data!r}"

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [TestMenu, AnotherTestMenu]
    # end def
# end class


@menus.register
class AnotherTestMenu(GotoMenu):
    title = "Sub Menu 2"
    description = lambda data: f'Something funny here.\n\nSUCH DATA\n{data!r}'

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [BackButton('back'), GotoButton(TestMenu, label='Got to the other Sub Menu.'), TestRadioMenu, TestCheckboxMenu]
    # end def
# end class


@menus.register
class TestMenu(GotoMenu):
    title = "Sub Menu"
    description = lambda data: f'We don\'d do sandwiches or public transport though.\n\nSUCH DATA\n{data!r}'

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [BackButton('back')]
    # end def
# end class


@menus.register
class TestCheckboxMenu(CheckboxMenu):
    title = "Shopping list"
    description = "The shopping list for today."

    @staticmethod
    def checkboxes(cls: CheckboxMenu) -> List[CheckboxButton]:
        return [
            CheckboxButton(title='Eggs', default_selected=True, value='eggs'),
            CheckboxButton(title='Milk', default_selected=False, value='milk'),
            CheckboxButton(title='Flux compensator', default_selected=False, value='flux'),
            CheckboxButton(title='LOVE', default_selected=False, value=None),
        ]
    # end def
# end class


@menus.register
class TestRadioMenu(RadioMenu):
    title = "Best Pony?"
    description = None

    # noinspection PyMethodMayBeStatic
    def radiobuttons(self) -> List[RadioButton]:
        return [
            RadioButton(title="Applejack", default_selected=False, value='aj'),
            RadioButton(title="Fluttershy", default_selected=False, value='fs'),
            RadioButton(title="Rarity", default_selected=False, value='rara'),
            RadioButton(title="Twilight", default_selected=False, value='ts'),
            RadioButton(title="Pinkie Pie", default_selected=False, value='pp'),
            RadioButton(title="Littlepip", default_selected=True, value='waifu'),
            RadioButton(title="Your Mom", default_selected=False, value='mom'),
            RadioButton(title="Changelings", default_selected=False, value='bug'),
            RadioButton(title="Cheesalys", default_selected=False, value='BUG'),
            RadioButton(title="Your face", default_selected=False, value=':('),
            RadioButton(title="Spike", default_selected=False, value='just_no'),
        ]
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
