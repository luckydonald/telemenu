#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from luckydonaldUtils.logger import logging

from telemenu.data import Data, MenuData
from telestate import TeleState

logging.add_colored_handler(logger_name=None, level=logging.DEBUG)
logger = logging.getLogger(__name__)

from os import environ
from typing import List, Union, Type, cast

from flask import Flask
from teleflask import Teleflask, abort_processing
from telestate.contrib.simple import SimpleDictDriver

from telemenu.menus import GotoMenu, Menu, RadioMenu, CheckboxMenu, TextStrMenu
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



@menus.states.ALL.on_command('start')
@abort_processing
def cmd_start(update: Update, data: str = None):
    MainMenu.show()
# end def


@bot.on_command('debug')
@abort_processing
def cmd_start(update: Update, data: str = None):
    DebugMenu.show()
# end def

@bot.on_command('cancel')
@abort_processing
def cmd_start(update: Update, data: str = None):
    state = menus.states.CURRENT
    menu = menus.get_current_menu()
    if menu:
        try:
            menu.refresh(done=True)
        except:
            logger.warning('marking menu as done failed.', exc_info=True)
    # end if
    menus.states.CURRENT.activate()
    return f"All actions aborted. No longer in state {state.name}."
# end def

@bot.on_update
def debug(update: Update):
    logger.info(f'Current state: {menus.states.CURRENT!r}')
    logger.info(f'Current messages listeners: {menus.states.CURRENT.update_handler.message_listeners!r}')
    logger.info(f'Current update listeners: {menus.states.CURRENT.update_handler.update_listeners!r}')
    logger.info(f'Global messages listeners: {menus.states.CURRENT.update_handler.teleflask.message_listeners!r}')
    logger.info(f'Global update listeners: {menus.states.CURRENT.update_handler.teleflask.update_listeners!r}')
# end def




@menus.register
class AnotherTestMenu(GotoMenu):
    title = "Sub Menu 2"
    description = 'Something funny would be here?'

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [BackButton('back'), GotoButton(DebugMenu, label='Got to the other Sub Menu.'), TestRadioMenu, TestCheckboxMenu]
    # end def
# end class


@menus.register
class DebugMenu(GotoMenu):
    title = "Debug Menu"

    @classmethod
    def description(cls, data):
        from pprint import pformat
        return 'We don\'d do sandwiches or public transport though.\n\nSUCH DATA\n{}'.format(pformat(data))
    # end def

    def menus(self) -> List[Union[ChangeMenuButton, Type[Menu]]]:
        return [BackButton('back')]
    # end def
# end class


@menus.register
class TestCheckboxMenu(CheckboxMenu):
    title = "Shopping list"
    description = "The shopping list for today."
    back = 'Back to the last one.'

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
class TheMainMenu(GotoMenu):
    title = "Home"
    description = "This is the main menu. Jump wherever you want."

    def menus(self):
        return [DebugMenu, MainMenu, AnotherTestMenu, TestRadioMenu]
    # end def
# end class


@menus.register
class TestRadioMenu(RadioMenu):
    title = "Best Pony?"
    description = "You selected: {data.menus[TEST_RADIO_MENU].data!r}"
    back = "Back"
    cancel = "Nope"
    done = "Done"

    def radiobuttons(self):
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


@menus.register
class MainMenu(GotoMenu):
    title = 'Main Menu'
    description = 'Please choose what you wanna do!'
    menus = lambda: [NewBotSubreddit]
# end def


@menus.register
class NewBotSubreddit(TextStrMenu):
    title = "Subreddit"
    description = "Heya, so you wanna create a new channel for all the reddit goodness?\nGreat! Let's get started! If you need to, you can abort at any time by sending /cancel.\n\nPlease send me the name of the reddit you wanna have in telegram."
    done = lambda: NewBotSort
    cancel = 'Cancel'
    # todo: Validate the subreddit for an valid and existing one.
# end class


@menus.register
class NewBotSort(RadioMenu):
    title = "Post Mode"
    cancel = 'Back'

    @classmethod
    def description(cls):
        reddit_name = cls.data.menus[NewBotSubreddit.id]
        reddit_link = f"https://reddit.com/r/{reddit_name}/"
        return (
            f'Got that. The <a href="{reddit_link}">{reddit_name}</a> subreddit it is.\n'
            '\n'
            'Do you want to post <code>hot</code>, <code>top</code> or <code>new</code> posts?\n'
            'We recommend choosing <code>hot</code>.'
        )
    # end def

    radiobuttons = lambda: [
        RadioButton(title='Hot', value='hot', default_selected=True),
        RadioButton(title='Top', value='top', default_selected=False),
        RadioButton(title='New', value='new', default_selected=False),
    ]

    @classmethod
    def done(cls):
        """
        The next variable is evaluated after all data processing is done,
        so it can react to the input data.
        In this case which element was chosen.
        """
        if cast(Data, cls.data).saved_data[NewBotSort.id] == 'top':
            # top needs selecting a duration
            return NewBotSelectHotTimeframe
        # end if
        # -> else -> skip directly to the media selection
        return NewChannelContentType
    # end def
# end def


@menus.register
class NewBotSelectHotTimeframe(RadioMenu):
    title = "Duration"
    cancel = 'Back'

    radiobuttons = [
        RadioButton(title='All', value='all'),
        RadioButton(title='Day', value='day'),
        RadioButton(title='Hour', value='hour'),
        RadioButton(title='Month', value='month'),
        RadioButton(title='Week', value='week'),
        RadioButton(title='Year', value='year'),
    ]
    done = lambda: NewChannelContentType
# end def


@menus.register
class NewChannelContentType(CheckboxMenu):
    title = "Media"
    description = "Cool. Now which content types do you want to have posted?"
    cancel = 'Back'

    checkboxes = [
        CheckboxButton(title='Text', value='text'),
        CheckboxButton(title='Images', value='image'),
        CheckboxButton(title='Albums', value='album'),
        CheckboxButton(title='Links', value='link'),
        CheckboxButton(title='Gifs', value='gif'),
        CheckboxButton(title='Videos', value='video'),
        CheckboxButton(title='Youtube', value='youtube'),
    ]
    done = MainMenu
# end class

