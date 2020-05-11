#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Usage:
API_KEY = "......";  from pytgbot.bot import Bot; bot = Bot(API_KEY); from luckydonaldUtils.logger import logging; logger = logging.getLogger(__name__); logging.add_colored_handler(level=logging.DEBUG);import sys;sys.path.extend(['.../r2tg/code/r2tg/telemenu_dist']);from telemenu.test import telemenu, teleflask, TestCheckboxMenu, Menu, TestTextUrlMenu, TestRadioMenu, RegisterTestMenu, Update, Message, Chat
"""
import re
import inspect
import unittest

from typing import List, Union, cast

from pytgbot.api_types.receivable.peer import Chat
from teleflask import Teleflask
from telestate import TeleState
from luckydonaldUtils.logger import logging
from telestate.contrib.simple import SimpleDictDriver
from pytgbot.api_types.receivable.updates import Update, Message
from pytgbot.api_types.sendable.reply_markup import ForceReply
from .data import MenuData, Data
from .menus import Menu, GotoMenu, CheckboxMenu, RadioMenu, TextStrMenu, TextIntMenu, TextFloatMenu
from .menus import TextPasswordMenu, TextEmailMenu, TextTelMenu, TextUrlMenu, UploadMenu
from .buttons import GotoButton, DoneButton, CheckboxButton, RadioButton
from .machine import TeleMenuMachine, TeleMenuInstancesItem

from .somewhere import API_KEY

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class Example(object):
    """
    Example for the different types of value retrieval we support for stuff like `title` etc.
    """

    # noinspection PyMethodMayBeStatic
    def var0(self, data: 'Data') -> str:
        return f"(0 normal def)\nPage {data.button_page}"
    # end def

    var1 = "(1 normal str)\nPage {data.button_page}"

    var2 = lambda data: "(2 lambda)\nPage " + str(data.button_page)

    @classmethod
    def var3(cls, data: 'Data') -> str:
        return "(3 classmethod)\nPage " + str(data.button_page)
    # end def

    var4: str

    @staticmethod
    def var5(data: 'Data') -> str:
        return "(5 classmethod)\nPage {page}".format(page=data.button_page)
    # end def

    # noinspection PyPropertyDefinition
    @property
    def var6(self, data: 'Data') -> str:
        return "(6 property)\nPage " + str(data.button_page)
    # end def

    var7 = "(7 str dot format)\nPage {data.button_page}".format

    @staticmethod
    def var8(data):
        return "(8 staticmethod)\nPage " + str(data.button_page)
    # end def

    def get_value_by_name(cls, key):
        return Menu.get_value_by_name(cls, key)
    # end def

    def assertEqual(self, a, b):
        assert a == b
    # end def

    def test_var0(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value_by_name('var0'), "(0 normal def)\nPage 123")
    # end def

    def test_var1(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value_by_name('var1'), "(1 normal str)\nPage 123")
    # end def

    def test_var2(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value_by_name('var2'), "(2 lambda)\nPage 123")
    # end def

    def test_var3(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value_by_name('var3'), "(3 classmethod)\nPage 123")
    # end def

    def test_var5(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value_by_name('var5'), "(5 classmethod)\nPage 123")
    # end def

    def test_var6(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value_by_name('var6'), "(6 property)\nPage 123")
    # end def
# end class


# ------------------------------
# TEST CLASSES
# here the stuff is implemented
# ------------------------------


teleflask = Teleflask(api_key=API_KEY)
telemenu = TeleMenuMachine(database_driver=SimpleDictDriver(), teleflask_or_tblueprint=teleflask)

telemenu.states.DEFAULT.on_command('start')
telemenu.states.DEFAULT.on_command('help')
def cmd_start(update: Update, text: Union[str, None]):
    RegisterTestMenu.send()
# end def


@telemenu.register
class RegisterTestMenu(Menu):
    # noinspection PyNestedDecorators
    @classmethod
    @TeleMenuMachine.mark_for_register.on_message
    def on_message_listener(cls, update: Update, msg: Message):
        """
        Handles callbackdata, registered by
        :param update:
        :return:
        """
        pass
    # end def

    @classmethod
    @TeleMenuMachine.mark_for_register.on_command('init')
    def on_command_listener(cls, update: Update, text: Union[str, None]):
        """
        Handles callbackdata, registered by
        :param update:
        :return:
        :return:
        """
        pass
    # end def
# end class


@telemenu.register
class TestMainMenu(GotoMenu):
    # noinspection PyMethodMayBeStatic
    def title(self):
        return "Where to go?"
    # end def

    # noinspection PyMethodMayBeStatic
    def description(self):
        return "Which text do you want to use?"
    # end def

    # noinspection PyMethodMayBeStatic
    def menus(self) -> List[GotoButton]:
        return [
            GotoButton(label='Checkbox', menu=TestCheckboxMenu, id='something_checkbox'),
            GotoButton(label='Radio Buttons', menu=TestRadioMenu, id=None),
            GotoButton(label='Text', menu=TestTextStrMenu),
            GotoButton(label='Int', menu=TestTextIntMenu),
            GotoButton(label='Password', menu=TestTextPasswordMenu),
            GotoButton(label='Email', menu=TestTextEmailMenu),
            GotoButton(label='Password', menu=TestTextPasswordMenu),
            GotoButton(label='Upload', menu=TestUploadMenu),
        ]
    # end def
# end class


@telemenu.register
class TestCheckboxMenu(CheckboxMenu):
    title = "Shopping list"
    description = "The shopping list for {now.format('dd.mm.yyyy')!s}"

    @staticmethod
    def checkboxes(cls: CheckboxMenu) -> List[CheckboxButton]:
        x: TeleMenuInstancesItem = cls._state_instance
        s: TeleState = x.state.CURRENT
        n: str = cls.id
        s.data = Data(menus={n: MenuData(message_id=123, page=0, )})
        return [
            CheckboxButton(title='Eggs', selected=True, value='eggs'),
            CheckboxButton(title='Milk', selected=False, value='milk'),
            CheckboxButton(title='Flux compensator', selected=False, value='flux'),
            CheckboxButton(title='LOVE', selected=False, value=None),
        ]
    # end def
# end class


@telemenu.register
class TestRadioMenu(RadioMenu):
    title = "Best Pony?"
    description = None

    # noinspection PyMethodMayBeStatic
    def radiobuttons(self) -> List[RadioButton]:
        return [
            RadioButton(title="Applejack", selected=False, value='aj'),
            RadioButton(title="Fluttershy", selected=False, value='fs'),
            RadioButton(title="Rarity", selected=False, value='rara'),
            RadioButton(title="Twilight", selected=False, value='ts'),
            RadioButton(title="Pinkie Pie", selected=False, value='pp'),
            RadioButton(title="Littlepip", selected=True, value='waifu'),
            RadioButton(title="Your Mom", selected=False, value='mom'),
            RadioButton(title="Changelings", selected=False, value='bug'),
            RadioButton(title="Cheesalys", selected=False, value='BUG'),
            RadioButton(title="Your face", selected=False, value=':('),
            RadioButton(title="Spike", selected=False, value='just_no'),
        ]
    # end def
# end class


@telemenu.register
class TestTextStrMenu(TextStrMenu):
    title = None
    description = "Tell me your name, please."

    done = lambda self: DoneButton(menu=TestTextEmailMenu),
# end class


@telemenu.register
class TestTextIntMenu(TextIntMenu):
    title = "Age"
    description = lambda self: "Tell me your age, please."

    def done(self):
        return DoneButton(menu=TestTextFloatMenu, label="Next field")
    # pass
# end class


@telemenu.register
class TestTextFloatMenu(TextFloatMenu):
    title = lambda self: "Height"
    description = "Please tell me your body height in centimeters"

    done = None
# end class


@telemenu.register
class TestTextPasswordMenu(TextPasswordMenu):
    title = "Password"
    description = "Set a password please."

    done = TestTextIntMenu
# end class


@telemenu.register
class TestTextEmailMenu(TextEmailMenu):
    title = "Email"
    description = "Set a email please."

    done = GotoButton(menu=TestTextPasswordMenu, label="Done"),
# end class


@telemenu.register
class TestTextTelMenu(TextTelMenu):
    title = "Email"
    description = "Set a email please."
# end class


@telemenu.register
class TestTextUrlMenu(TextUrlMenu):
    title = "URL"
    description = "What's your website?"
# end class


@telemenu.register
class TestUploadMenu(UploadMenu):
    title = "File"
    description = "Please upload an image."
    allowed_mime_types = [re.compile(r'image/.*')]

    done = DoneButton(TestMainMenu)
# end class

class BotMock(object):
    class BotMockFunc(object): pass

    def __getattr__(self, item):
        def function(*args, **kwargs):
            logger.debug(f'MOCK: called {item}(*{args}, **{kwargs})')
            return None
        # end def
        return function
    # end def
# end class


class UnitTests(unittest.TestCase):
    def test_state_change(self):
         self.assertEquals(telemenu.states.CURRENT, telemenu.states.DEFAULT, 'should start with default.')
         TestMainMenu.activate()
         self.assertNotEquals(telemenu.states.CURRENT, telemenu.states.DEFAULT, 'should not be default any longer.')
         self.assertEquals(telemenu.states.CURRENT, cast(TeleMenuInstancesItem, TestMainMenu._state_instance).state, 'current state should be state of activated menu.')
    # end def

    def test_state_change_2(self):
        telemenu.instances['TEST_MAIN_MENU'].menu.activate()
        self.assertEqual(telemenu.get_current_menu(), TestMainMenu)
        self.assertEqual(telemenu.instances[TestMainMenu.id].menu, telemenu.get_current_menu())
    # end def

    def test_get_property(self):
        telemenu.instances[TestMainMenu.id].menu.activate()
        self.assertEqual(telemenu.get_current_menu().get_value_by_name('title'), "Where to go?")
    # end def

    def foopr(self):
        telemenu.states.CURRENT.data
        telemenu.states.CURRENT
        telemenu.get_current_menu()
        telemenu.get_current_menu()
        telemenu.get_current_menu().get_value_by_name('title')
        telemenu.get_current_menu().get_value_by_name('title')
        telemenu.get_current_menu().title
        f = telemenu.get_current_menu().title
        inspect.signature(f)
        TestCheckboxMenu.activate()
        assert telemenu.get_current_menu().data.history == ['TEST_MAIN_MENU', 'TEST_CHECKBOX_MENU']
        telemenu.get_current_menu() == TestCheckboxMenu
        assert telemenu.get_last_menu() == TestMainMenu
        telemenu.get_last_menu(activate=True)
        assert telemenu.get_current_menu().data.history == ['TEST_MAIN_MENU']
        assert (
            telemenu.get_current_menu().get_value(telemenu.get_current_menu().text)
            ==
            telemenu.get_current_menu().get_value_by_name('text')
        )
        TestTextUrlMenu.activate()
        menu = telemenu.get_current_menu()
        assert isinstance(menu.reply_markup(), ForceReply)
        # ba = s.bind(telemenu.get_current_menu().menu, "!test")


# end class

from telestate import TeleStateMachine

# teleflask.process_update(Update(123, Message(456, 0, Chat(-123, 'private'))))

teleflask.process_update(Update(123, Message(456, 0, Chat(-123, 'private'), text="/cancel")))
teleflask.process_update(Update(123, Message(456, 0, Chat(-123, 'private'), text="/start wowsa")))

# menu = telemenu.get_current_menu()
# menu.send()
