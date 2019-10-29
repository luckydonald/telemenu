#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass, field as dataclass_field
from typing import Type, Dict, Union, List, ClassVar, Callable, Any, TypeVar, _tp_cache, Pattern, Optional

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if

T = TypeVar('T')  # Any type.
ClassValueOrCallable = Union[T, Callable[[Any], T]]

OptionalClassValueOrCallable = Union[ClassValueOrCallable, type(None)]
ClassValueOrCallableList = List[ClassValueOrCallable]


class Menu(object):
    title: OptionalClassValueOrCallable[str]
    description: OptionalClassValueOrCallable[str]
    done: OptionalClassValueOrCallable[Union['DoneButton', 'Menu']]  # it is possible to
# end class


class Button(object):
    label: ClassVar[str]
    id: ClassVar[Union[str, None]]  # None means automatic
# end class


@dataclass(init=False)
class GotoMenu(Menu):
    menus: ClassValueOrCallableList['GotoButton']
# end class


@dataclass
class GotoButton(Button):
    menu: ClassValueOrCallable[Menu]
# end class


@dataclass
class DoneButton(GotoButton):
    label: str = "Done"  # todo: multi-language
    id: Union[str, None] = None
# end class


@dataclass(init=False)
class CheckboxMenu(Menu):
    checkboxes: ClassValueOrCallable['CheckboxButton']
# end class


@dataclass
class CheckboxButton(Button):
    selected: ClassValueOrCallable[bool] = False
# end class


@dataclass(init=False)
class RadioMenu(Menu):
    radiobuttons: ClassValueOrCallable['RadioButton']    # TODO: check that max one has selected=True
# end class


class RadioButton(Button):
    pass
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
