#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import unittest

import json
import re
from abc import abstractmethod
from typing import Type, Union, List, Callable, TypeVar, cast
from telestate import TeleState
from dataclasses import dataclass
from luckydonaldUtils.typing import JSONType
from luckydonaldUtils.logger import logging
from telestate.contrib.simple import SimpleDictDriver
from teleflask.server.blueprints import TBlueprint
from pytgbot.api_types.sendable.reply_markup import ForceReply
from .data import MenuData, Data
from .menus import Menu, GotoMenu, CheckboxMenu, RadioMenu, TextStrMenu, TextIntMenu, TextFloatMenu, \
    TextPasswordMenu, TextEmailMenu, TextTelMenu, TextUrlMenu, UploadMenu
from .machine import TeleMenuMachine

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

T = TypeVar('T')  # Any type.
ClassValueOrCallable = Union[T, Callable[['Data'], T]]

OptionalClassValueOrCallable = Union[ClassValueOrCallable[T], type(None)]
ClassValueOrCallableList = List[ClassValueOrCallable[T]]


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


DEFAULT_PLACEHOLDER = object()


@dataclass(init=False, repr=True)
class TeleMenuInstancesItem(object):
    """
    This holds a menu and a telestate to register functions to.
    """
    machine: 'TeleMenuMachine'
    state: TeleState
    menu: Type['Menu']

    def __init__(self, machine: 'TeleMenuMachine', state: TeleState, menu: Type['Menu']):
        self.machine = machine
        self.state = state
        self.menu = menu
    # end def

    @property
    def global_data(self) -> 'Data':
        return Data.from_dict(self.state.data)
    # end def

    @property
    def state_data(self) -> 'MenuData':
        return self.global_data.menus[self.state.name]
    # end def
# end class


class CallbackData(object):
    type: str
    value: JSONType
    id: JSONType

    # noinspection PyShadowingBuiltins
    def __init__(self, type: str, id: JSONType = None, value: JSONType = None):
        self.type = type
        self.id = id
        self.value = value
    # end def

    def to_json_str(self):
        return json.dumps({'type': self.type, 'id': self.id, 'value': self.value})
    # end def

    @classmethod
    def from_json_str(cls, string):
        return cls(**json.loads(string))
    # end def

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'type={self.type!r}, '
            f'id={self.id!r}, '
            f'value={self.value!r}'
            ')'
        )
    # end def

    __str__ = __repr__
# end class


# end class


class ClassAwareClassMethodDecorator(object):
    """
    Decorator, but knowing the class in the end
    https://stackoverflow.com/a/54316392/3423324
    """
    def __init__(self, fn: Callable):
        logger.debug(f"received function {fn}.")
        self.fn = fn
    # end def

    def __set_name__(self, owner, name):
        # do something with owner, i.e.
        logger.debug(f"decorating {self.fn} as {name!r} on class {owner}.")
        # self.fn.class_name = owner.__name__

        # then replace ourself with the original method
        setattr(owner, name, self.decorate(function=self.fn, name=name, cls=owner))
    # end def

    # noinspection PyUnusedLocal
    @staticmethod
    @abstractmethod
    def decorate(function: Callable, name: str, cls: Type):
        return function
    # end def
# end class


class ClassAwareClassMethodDecorator2(object):
    """
    Decorator, but knowing the class in the end
    https://stackoverflow.com/a/54316392/3423324
    """
    def __init__(self, function: Callable):
        logger.debug(f"ClassAwareClassMethodDecorator2: received function {function!r}.")
        self.fn = function
    # end def

    def __call__(self, *args, **kwargs):
        logger.debug(f"ClassAwareClassMethodDecorator2: got called with {args!r} {kwargs!r}")
        return self.fn
    # end def

    def __set_name__(self, owner, name):
        # do something with owner, i.e.
        logger.debug(f"ClassAwareClassMethodDecorator2: decorating {self.fn} as {name!r} on class {owner}.")
        # self.fn.class_name = owner.__name__

        # then replace ourself with the original method
        setattr(owner, name, self.decorate(function=self.fn, name=name, cls=owner))
    # end def

    # noinspection PyUnusedLocal
    @staticmethod
    @abstractmethod
    def decorate(function: Callable, name: str, cls: Type):
        return function
    # end def
# end class


class menustate(ClassAwareClassMethodDecorator):
    class on_command_menustate(ClassAwareClassMethodDecorator):
        @staticmethod
        def decorate(function: Callable, name: str, cls: Type[Menu]):
            logger.success(f'REGISTEREING {function.__name__} as {name!r} to {cls.__name__}...')
            assert cls.tblueprint is not None
            return cast(TBlueprint, cls.tblueprint).on_command('TODO')(function)  # TODO
    # end class

    #class on_startup(ClassAwareClassMethodDecorator):
    #class add_startup_listener
    #class remove_startup_listener
# end class


# end class


class Button(object):
    """
    Other than the menus, buttons actually are instances as you can have multiple buttons in the same menu.
    Subclassing it would be way to much work, and providing values via constructor is everything we need really.

    Therefore here any function must be working with the current instance of the button.
    """
    id: Union[str, None] = None  # None means automatic

    @abstractmethod
    def get_label(self, data: Data):
        """ returns the text for the button """
        pass
    # end def

    @abstractmethod
    def get_callback_data(self, data: Data) -> CallbackData:
        """ returns the button data to identify the button. """
        pass
    # end def
# end class


# end class


class GotoButton(Button):
    menu: ClassValueOrCallable[Type[Menu]]
    label: ClassValueOrCallable[str]
    id: str

    def __init__(self, menu: Type[Menu], label=None):
        if label is None:
            label = menu.title
        # end if
        self.label = label
        self.menu = menu
    # end def

    @property
    def id(self) -> str:
        return self.menu.id
    # end def

    def get_callback_data(self, data: Data) -> CallbackData:
        return CallbackData(
            type=Menu.CALLBACK_BACK_BUTTON_TYPE,
            value=self.id,
        )
    # end def

    def get_label(self, data: Data):
        return self.label
    # end def
# end class


class DoneButton(GotoButton):
    label: ClassValueOrCallable[str] = "Done"  # todo: multi-language
    id: Union[str, None] = None

    def __init__(self, menu: Type[Menu], label=None):
        if label is None:
            label = self.__class__.label
        # end if
        super().__init__(menu, label=label)
    # end def
# end class


@dataclass
class BackButton(GotoButton):
    label: ClassValueOrCallable[str] = "Back"  # todo: multi-language
    id: Union[str, None] = None

    @property
    def id(self) -> str:
        return self.menu.id
    # end def

    def get_callback_data(self, data: Data) -> CallbackData:
        return CallbackData(
            type=Menu.CALLBACK_DONE_BUTTON_TYPE,
            value=self.id,
        )
    # end def
# end class


@dataclass
class CancelButton(GotoButton):
    label: ClassValueOrCallable[str] = "Cancel"  # todo: multi-language
    id: Union[str, None] = None
# end class


@dataclass(init=False, eq=False, repr=True)
class SelectableButton(Button):
    STATE_EMOJIS = {True: '1️⃣', False: '🅾️'}
    title: str
    value: JSONType
    default_selected: bool

    def __init__(
        self,
        title,
        value: JSONType,
        default_selected: bool = False
    ):
        self.title = title
        self.value = value
        self.default_selected = default_selected
    # end def

    @abstractmethod
    def get_selected(self, menu_data: MenuData) -> bool:
        pass
    # end def

    def get_label(self, menu_data: MenuData):
        """ returns the text for the button """
        return self.STATE_EMOJIS[self.get_selected(menu_data)] + " " + self.title
    # end def
# end def


# end def


# end class


class CheckboxButton(SelectableButton):
    STATE_EMOJIS = {True: "✅", False: "❌"}

    def get_selected(self, menu_data: MenuData) -> bool:
        if (
            self.value in menu_data.data and
            isinstance(menu_data.data, dict) and
            isinstance(menu_data.data[self.value], bool)
        ):
            return menu_data.data[self.value]
        # end if
        return self.default_selected
    # end def
# end class


# end class


class RadioButton(SelectableButton):
    STATE_EMOJIS = {True: "🔘", False: "⚫️"}

    def get_selected(self, menu_data: MenuData) -> bool:
        if (
            self.value in menu_data.data and
            isinstance(menu_data.data, str)
        ):
            return menu_data.data == self.value
        # end if
        return self.default_selected
    # end def
# end class


# end class


# end class


# end class


# end class


# end class


# end class


# end class


# end class


# end class


# end def


# ------------------------------
# TEST CLASSES
# here the stuff is implemented
# ------------------------------


telemenu = TeleMenuMachine(database_driver=SimpleDictDriver())


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

print('breakpoint')
telemenu.instances['TEST_MAIN_MENU']
telemenu.instances['TEST_MAIN_MENU'].menu
telemenu.instances['TEST_MAIN_MENU'].menu.activate()
print(telemenu.instances[TestMainMenu.id])
print(telemenu.get_current_menu())
assert telemenu.instances[TestMainMenu.id].menu == telemenu.get_current_menu()
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


class BotMock(object):
    class BotMockFunc(object): pass

    def __getattr__(self, item):
        def function(*args, **kwargs):
            logger.debug(f'MOCK: called {item}(*{args}, **{kwargs})')
            return None
        # end def
        return function
# end class


class UnitTests(unittest.TestCase):
    def test_state_change(self):
         telemenu.states.CURRENT
         self.assertEquals(telemenu.states.CURRENT, telemenu.states.DEFAULT, 'should start with default.')
         TestMainMenu.activate()
         self.assertNotEquals(telemenu.states.CURRENT, telemenu.states.DEFAULT, 'should not be default any longer.')
         self.assertEquals(telemenu.states.CURRENT, TestMainMenu._state_instance, 'current state should be state of activated menu.')
    # end def
# end class
