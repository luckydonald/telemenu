# -*- coding: utf-8 -*-
import json
from abc import ABC, ABCMeta
from typing import Type, List, Union, Dict, Callable, ClassVar, TypeVar, Generic, Any

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from pytgbot import Bot
from pytgbot.api_types.receivable.updates import Update
from pytgbot.api_types.sendable.reply_markup import Button, KeyboardButton, InlineKeyboardButton, ForceReply, \
    ReplyKeyboardMarkup
from pytgbot.api_types.sendable.reply_markup import ReplyMarkup, InlineKeyboardMarkup
from teleflask.new_messages import TextMessage, SendableMessageBase
from teleflask.server.base import TeleflaskMixinBase
from teleflask.server.mixins import StartupMixin

from telestate import TeleState, TeleMachine
from .buttons import GotoMenuButton, ToggleButton, GotoStateButton

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


T = TypeVar('T')  # Any type.
ClassValueOrCallable = ClassVar[Union[T, Callable[[TeleState, Update], T]]]


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
            - Update state to the one of the next Menu.

    """
    state: TeleState
    # state: Union[TeleState, Callable[[TeleState], TeleState]]

    title: ClassValueOrCallable[str]  # will be bold
    title: str
    @classmethod
    def title(cls, state: TeleState, update: Update) -> str:
        raise NotImplementedError('Subclass must implement this.')
    # end def

    description: ClassValueOrCallable[str]  # html
    description: str  # html
    @classmethod
    def description(cls, state: TeleState, update: Update) -> str:
        raise NotImplementedError('Subclass must implement this.')
    # end def

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

    def output_current_menu(self, meta_data: Dict[str, JSONType]):
        raise NotImplementedError('Subclasses should implement this')
    # end def

    def create_for_state(self, state: TeleState):
        data = self.prepare_meta(state)
    # end def

    def format_text(self, title: str, description: str) -> str:
        return (
            f"<b>{title}</b>\n"  # TODO: escape, check if callable
            f"{description}"
        )
    # end def

    def process_update(self, update):
        raise NotImplementedError('Subclasses should implement this')
    # end def

    def do_startup(self):
        super().do_startup()
    # end def
# end class


class AnswerMenu(Menu):
    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        data = super().prepare_meta(state)
        return data
    # end def

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message where a user will answer to.

        :param meta_data:  Result of `self.prepare_meta(state=state)`.
        :return: Message to send.
        """
        return TextMessage(
            text=self.format_text(meta_data['title'], meta_data['description']),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=ForceReply(selective=True),
        )
    # end def

    def process_update(self, update):
        pass
    # end def

    def answer_parser(self, state: TeleState, text: str) -> Any:
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class


class ButtonMenu(Menu, ABC):
    type: Union[Type[Button], Type[KeyboardButton], Type[InlineKeyboardButton]]
    buttons: ClassValueOrCallable[List[Union[GotoMenuButton, GotoStateButton, ToggleButton]]]

    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        data = super().prepare_meta(state)
        return {
            **data,
            "type": self.type.__name__,
            "buttons": self.buttons(state) if callable(self.buttons) else self.buttons,
        }
    # end def
# end class


class InlineButtonMenu(ButtonMenu, ABC):
    """
    Text message directly has some buttons attached.
    """
    type: Type = InlineKeyboardButton

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message with the menu.

        :param meta_data:  Result of `self.prepare_meta(state=state)`.
        :return: Message to send
        """
        return TextMessage(
            text=self.format_text(meta_data['title'], meta_data['description']),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=meta_data['buttons'],
            ),
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

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message with the menu.

        :param meta_data:  Result of `self.prepare_meta(state=state)`.
        :return: Message to send
        """
        return TextMessage(
            text=self.format_text(meta_data['title'], meta_data['description']),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=meta_data['buttons'],
                resize_keyboard=True,  # make smaller if not needed
                one_time_keyboard=True,  # remove after click
                selective=True,  # only the user
            ),
        )
    # end def

    def process_update(self, update):
        return super().process_update(update)
    # end def

    type = KeyboardButton
    buttons: List[GotoMenuButton]

    def answer_parser(self, state: TeleState, text: str) -> Any:
        """
        Function being called if no of the existing buttons matched.
        :param state:
        :param text:
        :return:
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class

