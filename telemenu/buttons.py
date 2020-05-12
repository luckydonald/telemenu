#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from abc import abstractmethod
from dataclasses import dataclass
from typing import Union, Type

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

from luckydonaldUtils.typing import JSONType

from . import ClassValueOrCallable
from .data import Data, MenuData, CallbackData

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


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

class ChangeMenuButton(Button):
    """
    Base class for switching menus.
    """
    label: ClassValueOrCallable[str]

    def __init__(self, label: str):
        self.label = label
    # end def

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError('Subclass must implement this.')
    # end def

    @abstractmethod
    def get_callback_data(self, data: Data) -> CallbackData:
        raise NotImplementedError('Subclass must implement this.')
    # end def

    def get_label(self, data: Data):
        return self.label
    # end def
# end class


class GotoButton(ChangeMenuButton):
    menu: ClassValueOrCallable[Type['telemenu.menus.Menu']]
    label: ClassValueOrCallable[str]

    def __init__(self, menu: Type['telemenu.menus.Menu'], label=None):
        if label is None:
            label = menu.title
        # end if
        super().__init__(label=label)
        self.menu = menu
    # end def

    @property
    def id(self) -> str:
        return self.menu.id
    # end def

    def get_callback_data(self, data: Data) -> CallbackData:
        from .menus import Menu
        return CallbackData(
            type=Menu.CALLBACK_GOTO_BUTTON_TYPE,
            value=self.id,
        )
    # end def
# end class


class DoneButton(ChangeMenuButton):
    def __init__(self, label: str = 'Done'):
        super().__init__(label=label)
    # end def

    @property
    def id(self) -> str:
        return ''
    # end def

    def get_callback_data(self, data: Data) -> CallbackData:
        from .menus import Menu
        return CallbackData(
            type=Menu.CALLBACK_DONE_BUTTON_TYPE,
            value=self.id,
        )
    # end def
# end class


@dataclass(init=False)
class BackButton(ChangeMenuButton):
    label: ClassValueOrCallable[str]

    def __init__(self, label: str = "Back"):    # todo: multi-language for label
        super().__init__(label=label)
        self.label = label
    # end def

    @property
    def id(self) -> str:
        return ''
    # end def

    def get_callback_data(self, data: Data) -> CallbackData:
        from .menus import Menu
        return CallbackData(
            type=Menu.CALLBACK_BACK_BUTTON_TYPE,
            value=self.id,
        )
    # end def
# end class


class CancelButton(GotoButton):
    def __init__(self, label: str = "Cancel"):    # todo: multi-language for label
        super().__init__(menu=None, label=label)
        self.label = label
    # end def

    @property
    def id(self) -> str:
        return ''
    # end def

    def get_callback_data(self, data: Data) -> CallbackData:
        from .menus import Menu
        return CallbackData(
            type=Menu.CALLBACK_CANCEL_BUTTON_TYPE,
            value=self.id,
        )
    # end def
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
