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
ClassValueOrCallable = ClassVar[Union[T, Callable[[Update], T]]]


class Menu(StartupMixin, TeleflaskMixinBase):
    """
    Menu for telegram (flask).
    Basically a TBlueprint, which will select the current state and process only those functions.

    It will load/save the state before/after processing the updates via the functions `load_state_for_chat_user` and `save_state_for_chat_user`.
    Those functions must be implemented via an extending subclass, so you can use different storage backends.

    Variables:
    - state.*
    - <placeholder for selected answer>
        - selected choice (especially as we remove the buttons if done)
        - multiple choices (if multiple checkboxes)
        - text (not as important, as your message is there)
    - Metadata: (user_link, chat, time)
        - same as t.me/RulesRulesBot

    There are the following steps:

    - Create new menu
        - Use cases:
            - Menu should be displayed (i.e. we are executing /open_menu)
        - Steps:
            - Generate      title, body, buttons  (`prepare_meta`)
            - Store         title, body, buttons, so actions can work later
            - Send Message  title, body, buttons  (`output_current_menu`)
            - Store Message ID (or full update?)
            - Update State to the Menu's state, listening for updates.
    - Edit existing menu
        - Use cases:
            - User toggles checkbox
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
            - Update state to the one of the next Menus, or a specific state (/cancel: state DEFAULT).

    Approaches:
        - Mix and match button types
            - probably a bad idea because it's very complex.
            - also storage of multiple different types per page would be aweful.
        - Fixed Menu types
            - Features:
                - Automatic pagination for all of those with too many buttons ≪/≫ (or maybe one of ⋘/⋙, ⏪/⏩, ◀️/▶️ or ⬅️/➡️)
                    - maybe first/last as well? ↖️/↘️, ⏮/⏭, 🔙/🔜, ⋘/⋙
                    - space for numbered pagination?
                        - e.g. [⋘|≪|2|3|4|≫|⋙]
                            - No emoji versions of numbers, they would go only up to 10: 2️⃣|3️⃣|4️⃣|...|9️⃣|🔟
                - "Back to last menu" button: ⏏️, 🆙, 🛑, 🔙, ⃠, 🤚, 🚫 or simply Back
                    - edits menu in place (if possible)
                    - pops last entry from history-hierarchy.
                - Automated data storage?
                    - checkboxes, text fields, dates, ... get variable names (to write to state.name) assigned
                        - a bit like argparse
                        - support multiple levels like state.dict.dict2.foo.bar
                    - what about files? base64?
            - Types:
                - Menu
                    - switch to another menu
                        - append to history-hierarchy.
                    - basically edits the current message (if possible) to display a different menu
                - Checkboxes (Toggle on/off) ❌/✅ — Aka. Multi-select
                    - Nullable Checkboxes (Toggle null/on/off) ❔/❌/✅ (Or maybe one of 🆓, 0️⃣, ➖ or ␀ ?)
                - Radio Buttons (Only one can be on) 🔘/⚪️ — Aka. Dropdown
                - Text input
                    - Predefined parsers (see html <input type="..."/>)
                        - text: unmodified
                        - number: int()
                        - float: float()
                        - password: attempt to delete the user's message and edit in a ••••• version into the answer.
                        - email: text with abc@uvw.xyz
                        - date: see 'Datepicker' below.
                        - month: see 'Datepicker' below.
                        - radio: see 'Radio Buttons' above.
                        - checkbox: see 'Checkboxes' above.
                        - search: see 'text', maybe inline
                        - tel: something in some number format.
                        - time: see 'Datepicker' below
                        - url: valid looking URL, maybe optionally http(s) only?
                        - week: see 'Datepicker' below
                - File Upload:
                    - html <input type="..."/> like :
                        - file
                    - optional list of accepted mimetype
                        - maybe tuples ('application', 'pdf'), ('text', None)
                        - or glob like  'application/pdf'  and  'text/*'
                        - regex maybe?  'application/pdf'  and  'text/[\\w-]+'
                - Datepicker: make a calender grid with the buttons, also allow text input.
                    - html <input type="..."/> like :
                        - date: year, month, day, no time(zone)
                            - format settable
                            - US, DE, ...
                            - own format string
                        - month:  month and year control, no time(zone)
                        - week:  week and year, no time(zone)
                        - time:  hours and minute, no timezone
                    - single components:
                        - year (buttons + num text)
                        - month (buttons + text (num or string))
                        - day (buttons + num text)
                        - weekday (buttons + text string)
                        - hour (buttons + num text)
                        - minute (buttons + num text)
                        - second (buttons + num text)
                        - timezone (buttons + num text)
                - Search: Use inline search?


    """
    state: TeleState
    # state: Union[TeleState, Callable[[TeleState], TeleState]]

    title: ClassValueOrCallable[str]
    title: str
    @classmethod
    def title(cls, update: Update) -> str:
        """
        Function returning the title to use.
        You can also set the title directly to a string, `title = 'foobar', instead of a `def title(self, update)` returning a string.

        The title is made bold, by wrapping the text into `<b>` and `</b>`.
        Note: You need to make sure the html is escaped where needed.

        The update is provided via parameter, also the function has access to the curret state (`self.state`).

        :param update: The telegram update which causes this menu to be rendered (e.g. a command, a click on the previous menu, etc.)
        :return:
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def

    description: ClassValueOrCallable[str]  # html
    description: str  # html
    def description(cls, update: Update) -> str:
        """
        Function returning the description to use.
        You can also set the description directly to a string, `description = 'foobar', instead of a `def description(self, update)` returning a string.

        Note: You need to make sure the html is escaped where needed.

        The update is provided via parameter, also the function has access to the curret state (`self.state`).

        :param update: The telegram update which causes this menu to be rendered (e.g. a command, a click on the previous menu, etc.)
        :return:
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def

    def __init__(self, telemachine: TeleMachine):
        super().__init__()
        if self.state is None:
            name = self.create_state_name(self.__class__.__name__)
            logger.debug(f'creating state for menu {self.__class__.__name__}: {name}')
            self.state = TeleState(name)
            telemachine.register_state(name, self.state)
        # end if
    # end def

    def prepare_meta(self, update: Update) -> Dict[str, JSONType]:
        """
        Prepares the data for usage in `output_current_menu`.

        :return: The dict with the prepared texts.
        """
        return {
            "title": self.title(update) if callable(self.title) else self.title,
            "description": self.description(update) if callable(self.description) else self.description,
        }
    # end def

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Generates a message for this menu.

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
        :return: Message to send
        """
        raise NotImplementedError('Subclasses should implement this')
    # end def

    # noinspection PyMethodMayBeStatic
    def format_text(self, title: str, description: str) -> str:
        """
        Formats a text containing tile and description in html.
        :param title:
        :param description:
        :return:
        """
        return (
            f"<b>{title}</b>\n"
            f"{description}"
        )
    # end def

    @staticmethod
    def create_state_name(cls_name):
        """
        Generates a name for the state to use, based on the class's name.

        :param cls_name:
        :return:
        """
        return f'__TELEMENU__{cls_name.upper()}'
    # end def

    def process_update(self, update):
        raise NotImplementedError('Subclasses should implement this')
    # end def

    def do_startup(self):
        super().do_startup()
    # end def
# end class


class AnswerMenu(Menu):
    def title(self, update: Update) -> str:
        return super().title(update)
    # end def

    def description(self, update: Update) -> str:
        return super().description(update)
    # end def

    def prepare_meta(self, state: TeleState) -> Dict[str, JSONType]:
        data = super().prepare_meta(state)
        return data
    # end def

    def output_current_menu(self, meta_data: Dict[str, JSONType]) -> SendableMessageBase:
        """
        Sends a text message where a user will answer to.

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
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

    def answer_parser(self, update: Update, text: str) -> Any:
        """
        Function being called to parse the text the user sent us in response.

        :param update: The answering update (text message, button press, etc.)
        :param text:   The extracted text.
        :return: A parsed value of the required format.
        """
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

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
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

        :param meta_data:  Result of `self.prepare_meta(update=update)`.
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

    def answer_parser(self, update: Update, text: str) -> Any:
        """
        Function being called if no of the existing buttons matched.

        :param update: The answering update (text message, button press, etc.)
        :param text:   The extracted text.
        :return: A parsed value of the required format.
        """
        raise NotImplementedError('Subclass must implement this.')
    # end def
# end class

