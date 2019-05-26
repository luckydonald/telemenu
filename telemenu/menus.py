# -*- coding: utf-8 -*-
import json
from abc import ABC, ABCMeta
from collections import Callable
from typing import Type, List, Union, Dict

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from paramiko.py3compat import is_callable
from pytgbot import Bot
from pytgbot.api_types.receivable.updates import Update
from pytgbot.api_types.sendable.reply_markup import Button, KeyboardButton, InlineKeyboardButton
from pytgbot.api_types.sendable.reply_markup import ReplyMarkup, InlineKeyboardMarkup
from teleflask.server.base import TeleflaskMixinBase
from teleflask.server.mixins import StartupMixin

from telestate import TeleState, TeleMachine
from .buttons import MenuButton

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class MenuMachine(object):
    def output_current_menu(self):
        pass
    # end def
# end class


class Menu(StartupMixin, TeleflaskMixinBase):
    """
    Menu for telegram (flask).
    Basically a TBlueprint, which will select the current state and process only those functions.

    It will load/save the state before/after processing the updates via the functions `load_state_for_chat_user` and `save_state_for_chat_user`.
    Those functions must be implemented via an extending subclass, so you can use different storage backends.

    There are the following steps:

    - Create new menu
        - Use cases:
            - Menu should be displayed (i.e. we are executing /open_menu)
        - Steps:
            - Generate      title, body, buttons  (`prepare_meta`)
            - Store         title, body, buttons
            - Send Message  title, body, buttons  (`output_current_menu`)
            - Store Message ID (or via update?)
            - Update State to the Menu's state, listening for updates.
    - Edit existing menu
        - Use cases:
            - Uer toggles checkbox
            - User clicks pagination
        - Steps:
            - Listen for events
            - On event (e.g. inline button):
            - Load existing menu from state:  title, body, buttons
                - Find current menu
                - Create object from existing data (`self(**data)`)
            - Transform changes
                - Pagination
                - Checkbox
            - Store updated data
            - Edit Message  title, body, buttons  (`output_current_menu`)
    - Leave menu
        - Use cases:
            - /cancel
            - Navigation to a different menu
        - Steps
            - Listen for events
            - On event (e.g. inline button):
            - Load existing menu from state:  title, body, buttons
                - Find current menu
                - Create object from existing data (`self(**data)`)
            - Close Menu
                - Remove Buttons
                - Edit text to include chosen answer
                - or maybe: Delete completely
            - Update state to the one of the new Menu.

    """
    state: TeleState
    title: str  # bold
    description: str  # html

    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        return {
            "title": self.title(state) if callable(self.title) else self.title,
            "description": self.description(state) if callable(self.description) else self.description,
        }
    # end def

    def __init__(self, telemachine: TeleMachine):
        if self.state is None:
            name = "__TELEMENU_" + self.__class__.__name__
            self.state = TeleState(name)
            telemachine.register_state(name, self.state)
        # end if
    # end def

    def output_current_menu(self) -> List[List[Button]]:
        raise NotImplementedError('Subclasses should implement this')
    # end def

    def create_for_state(self, state: TeleState):
        data = self.prepare_meta(state)
    # end def

    def format_text(self) -> str:
        return (
            f"<b>{self.title}</b>\n"  # TODO: escape, check if callable
            f"{self.description}"
        )
    # end def

    def process_update(self, update):
        raise NotImplementedError('Subclasses should implement this')
    # end def

    def do_startup(self):
        raise NotImplementedError('Subclasses should implement this')
    # end def
# end class


class ButtonMenu(Menu, ABC):
    type: Union[Type[Button], Type[KeyboardButton], Type[InlineKeyboardButton]]
    buttons: List[MenuButton]

    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        data = super().prepare_meta(state)
        return {
            **data,
            "type": self.type.__name__,
            "buttons": self.buttons if not isinstance(self.buttons, Callable) else self.buttons(state),
        }
    # end def

    def do_startup(self):
        super().do_startup()
    # end def
# end class


class InlineButtonMenu(ButtonMenu, ABC):
    """
    Text message directly has some buttons attached.
    """
    type: Type = InlineKeyboardButton
    buttons: List[MenuButton]
    _data: Dict[str, JSONType]

    def output_current_menu(self):
        bot: Bot
        bot.send_message(
            chat_id=123,
            reply_to_message_id=123,
            text=self.format_text(),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=InlineKeyboardMarkup(self.buttons())
        )
    # end def

    def process_update(self, update: Update):
        if not (update and update.callback_query and update.callback_query.data):
            # skip this menu
            return super().process_update(update)
        # end def
        assert update.callback_query.data
        data = json.loads(update.callback_query.data)

        # TODO

    # end def
# end class


class SendButtonMenu(ButtonMenu):
    """
    Send button menu is like a InlineButtonMenu, but replaces the user keyboard with buttons.
    This means the user could still enter his own value if he so desire.

    If a text doesn't match the provided buttons a custom `parse_text` function is called to get the result.
     """

    def output_current_menu(self) -> List[List[Button]]:
        pass

    def process_update(self, update):
        pass

    def do_startup(self):
        pass

    type = KeyboardButton
    buttons: List[MenuButton]

    def parse_text(self, text):
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class

