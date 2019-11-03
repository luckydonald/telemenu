#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import inspect_mate
from html import escape
from types import LambdaType, BuiltinFunctionType
from typing import Type, Dict, Union, List, ClassVar, Callable, Any, TypeVar, _tp_cache, Pattern, Optional
from dataclasses import dataclass, field as dataclass_field
from luckydonaldUtils.logger import logging
from pytgbot import Bot
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardMarkup, InlineKeyboardButton

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

T = TypeVar('T')  # Any type.
ClassValueOrCallable = Union[T, Callable[[Any], T]]

OptionalClassValueOrCallable = Union[ClassValueOrCallable, type(None)]
ClassValueOrCallableList = List[ClassValueOrCallable]


class Example(object):
    def var0(self, a):
        return "0" + a
    # end def

    var1 = "1"

    var2 = lambda a: "2" + a

    @classmethod
    def var3(cls, a):
        return "3" + a
    # end def

    var4: str

    @staticmethod
    def var5(a):
        return "5" + a
    # end def

    @property
    def var6(self, a):
        return "6" + a
    # end def

    var7 = "test".format
# end class

_button_id = "CURRENT_STATE.action.<action-type>.<index>;<payload>"  # normal action state
_button_id = "CURRENT_STATE.action.goto.1;"  # normal action state
_button_id = "CURRENT_STATE.page.2"  # pagination

Fuuu = object()


class Menu(object):
    """
    A menu is a static construct holding all the information.
    It is static, so any method should work without having any instance.

    That is because you create a subclass for every menu you need,
    and overwrite functions and or class variables.
    That way there will only ever one 'instance' needed per class,
    and everything could be handled as singleton, which a static class already is.
    (Not doing the same mistake some other libs here (Looking angrily at you, Codeigniter))
    """
    title: OptionalClassValueOrCallable[str]
    description: OptionalClassValueOrCallable[str]
    done: OptionalClassValueOrCallable[Union['DoneButton', 'Menu']]

    @classmethod
    def get_text(cls):
        text = ""
        title = cls.get_value('title')
        if title:
            text += f"<b>{escape(title)}</b>\n"
        # end if
        description = cls.get_value('description')
        if description:
            text += f"{escape(description)}\n"
        # end if
        # text += f"<i>Selected: {escape(description)}</i>\n"
        return text
    # end def

    @classmethod
    def get_done_button(cls):
        done: Union[DoneButton, Menu] = cls.get_value('done')
        if isinstance(done, DoneButton):
            return InlineKeyboardButton(
                text=done.label,
                callback_data=f"{cls.__class__.__name__}__done__{done.get_id()}",
            )
        elif isinstance(done, Menu):
            return InlineKeyboardButton(
                text=done.title,
                callback_data=f"{cls.__class__.__name__}__done__{done.get_id()}",
            )
        # end if
    # end def

    @classmethod
    def get_own_buttons(cls) -> List[InlineKeyboardButton]:
        return []
    # end def

    @classmethod
    def get_value(cls, key):
        value = getattr(cls, key, Fuuu)
        if value == Fuuu:
            raise KeyError(f'Key {key!r} not found.')
        # end if

        params = dict(state=None, user=None, chat=None)
        if isinstance(value, str):
            return value.format(**params)
        # end if
        if isinstance(value, BuiltinFunctionType):
            # let's assume you wrote `some_var = "...".format`
            return value(**params)
        # end if
        if inspect_mate.is_class_method(cls, key):
            return value(cls, **params)
        # end if
        if inspect_mate.is_regular_method(cls, key):
            return value(None, **params)
        # end if
        if inspect_mate.is_static_method(cls, key):
            return value(**params)
        # end if
        if inspect_mate.is_property_method(cls, key):
            return value.fget(None, **params)
        # end if
        if isinstance(value, LambdaType):
            return value(**params)
        # end if

        # if all that didn't work, just return it.
        return value
    # end def

    @classmethod
    def get_id(cls) -> str:
        return "menu@id:" + cls.id if hasattr(cls, 'id') and cls.id else "menu@class:" + cls.__name__
    # end def
# end class


class Button(object):
    """
    Other than the menus, buttons actually are instances as you can have multiple buttons in the same menu.
    Subclassing it would be way to much work, and providing values via constructor is everything we need really.

    Therefore here any function must be working with the current instance of the button.
    """
    label: ClassValueOrCallable[str]
    id: Union[str, None] = None  # None means automatic

    def get_id(self) -> str:
        return "button@id:" + self.id if hasattr(self, 'id') and self.id else "button@class:" + self.__class__.__name__
    # end def
# end class


@dataclass(init=False)
class GotoMenu(Menu):
    menus: ClassValueOrCallableList['GotoButton']

    def get_keyboard(self) -> InlineKeyboardMarkup:
        menus: List[GotoButton] = self.get_value('menus')
        return InlineKeyboardMarkup(
            inline_keyboard=[
                InlineKeyboardButton(
                    text=button.label,
                    callback_data=f"{self.__class__.__name__}__goto__{button.get_id()}",
                )
                for i, button in enumerate(menus)
            ]
        )
    # end def

    def send_message(self, chat_id):
        bot = Bot()
        bot.send_message(chat_id=chat_id, text=f"<b>{self.title}</b>\n{self.description}")
# end class


@dataclass
class GotoButton(Button):
    menu: ClassValueOrCallable[Menu]
    label: ClassValueOrCallable[str]
    id: Union[str, None] = None

    def get_id(self) -> str:
        return self.id if self.id else 'button@menu:' + self.menu.get_id()+";"+self.label
    # end def
# end class


@dataclass
class DoneButton(GotoButton):
    label: ClassValueOrCallable[str] = "Done"  # todo: multi-language
    id: Union[str, None] = None
# end class


@dataclass(init=False)
class CheckboxMenu(Menu):
    checkboxes: ClassValueOrCallable['CheckboxButton']
# end class


@dataclass
class CheckboxButton(Button):
    label: ClassValueOrCallable[str]
    id: Union[str, None] = None  # None means automatic
    selected: ClassValueOrCallable[bool] = False
# end class


@dataclass(init=False)
class RadioMenu(Menu):
    radiobuttons: ClassValueOrCallable['RadioButton']    # TODO: check that max one has selected=True
# end class


@dataclass
class RadioButton(Button):
    label: ClassValueOrCallable[str]
    id: Union[str, None] = None  # None means automatic
    selected: ClassValueOrCallable[bool] = False
# end class


@dataclass(init=False)
class TextMenu(Menu):
    def _parse(self, text: str) -> Any:
        raise NotImplementedError('Subclasses must implement that.')
    # end def
# end class


class TextStrMenu(TextMenu):
    def _parse(self, text: str) -> str:
        return text
    # end def
# end class


class TextIntMenu(TextMenu):
    def _parse(self, text: str) -> int:
        return int(text)
    # end def
# end class


class TextFloatMenu(TextMenu):
    def _parse(self, text: str) -> float:
        return float(text)
    # end def
# end class


class TextPasswordMenu(TextMenu):
    def _parse(self, text: str) -> str:
        return text
    # end def
# end class


class TextEmailMenu(TextMenu):
    def _parse(self, text: str) -> str:
        if "@" not in text or "." not in text:  # TODO: improve validation.
            raise ValueError('No good email.')
        return text
    # end def
# end class


class TextTelMenu(TextMenu):
    def _parse(self, text: str) -> str:
        # TODO: add validation.
        return text
    # end def
# end class


@dataclass(init=False)
class TextUrlMenu(TextMenu):
    allowed_protocols: List[str] = dataclass_field(default_factory=lambda: ['http', 'https'])

    def _parse(self, text: str) -> str:
        if not any(text.startswith(protocol) for protocol in self.allowed_protocols):
            raise ValueError('Protocol not allowed')
        # end if
        # TODO: improve validation.
        return text
    # end def
# end class


@dataclass(init=False)
class UploadMenu(Menu):
    allowed_mime_types: Union[List[Union[str, Pattern]], None] = None
    allowed_extensions: Union[List[str], None] = None
# end def


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


class TestCheckboxMenu(CheckboxMenu):
    title = "Shopping list"
    description = "The shopping list for {now.format('dd.mm.yyyy')!s}"

    # noinspection PyMethodMayBeStatic
    def checkboxes(self) -> List[CheckboxButton]:
        return [
            CheckboxButton(label='Eggs', selected=True, id='eggs'),
            CheckboxButton(label='Milk', selected=False, id='eggs'),
            CheckboxButton(label='Flux compensator', selected=False, id='flux'),
            CheckboxButton(label='LOVE', selected=False, id=None),
        ]
    # end def
# end class


class TestRadioMenu(RadioMenu):
    title = "Best Pony?"
    description = None

    # noinspection PyMethodMayBeStatic
    def radiobuttons(self) -> List[RadioButton]:
        return [
            RadioButton(label="Applejack", selected=False, id='aj'),
            RadioButton(label="Fluttershy", selected=False, id='fs'),
            RadioButton(label="Rarity", selected=False),
            RadioButton(label="Twilight", selected=False, id='ts'),
            RadioButton(label="Rainbow Dash", selected=False),
            RadioButton(label="Littlepip", selected=True, id='waifu'),
        ]
    # end def
# end class


class TestTextStrMenu(TextStrMenu):
    title = None
    description = "Tell me your name, please."

    done = lambda self: DoneButton(menu=TestTextEmailMenu),
# end class


class TestTextIntMenu(TextIntMenu):
    title = "Age"
    description = lambda self: "Tell me your age, please."

    def done(self):
        return DoneButton(menu=TestTextFloatMenu, label="Next field")
    # pass
# end class


class TestTextFloatMenu(TextFloatMenu):
    title = lambda self: "Height"
    description = "Please tell me your body height in centimeters"

    done = None
# end class


class TestTextPasswordMenu(TextPasswordMenu):
    title = "Password"
    description = "Set a password please."

    done = TestTextIntMenu
# end class


class TestTextEmailMenu(TextEmailMenu):
    title = "Email"
    description = "Set a email please."

    done = DoneButton(menu=TestTextPasswordMenu),
# end class


class TestTextTelMenu(TextTelMenu):
    title = "Email"
    description = "Set a email please."
# end class


class TestTextUrlMenu(TextUrlMenu):
    title = "URL"
    description = "What's your website?"
# end class


class TestUploadMenu(UploadMenu):
    title = "File"
    description = "Please upload an image."
    allowed_mime_types = [re.compile(r'image/.*')]

    done = DoneButton(menu=TestTextPasswordMenu)
# end class
