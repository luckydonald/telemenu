# -*- coding: utf-8 -*-
import json
from typing import Type, List, Union

from luckydonaldUtils.logger import logging
from pytgbot import Bot
from pytgbot.api_types.receivable.updates import Update
from pytgbot.api_types.sendable.reply_markup import Button, KeyboardButton, InlineKeyboardButton, ReplyMarkup
from teleflask.server.base import TeleflaskMixinBase
from teleflask.server.mixins import StartupMixin

from telestate import TeleState
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
    """
    state: TeleState
    title: str  # bold
    description: str  # html

    def output_current_menu(self):
        raise NotImplementedError('Subclassses should implement this')
    # end def

    def format_text(self):
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



class ButtonMenu(Menu):
    type: Union[Type[Button], Type[KeyboardButton], Type[InlineKeyboardButton]]
    buttons: List[MenuButton]
# end class


class InlineButtonMenu(ButtonMenu):
    """
    Text message directly has some buttons attached.
    """
    type = InlineKeyboardButton
    buttons: List[MenuButton]

    def output_current_menu(self):
        bot: Bot
        bot.send_message(
            chat_id=123,
            reply_to_message_id=123,
            text=self.format_text(),
            parse_mode="html",
            disable_web_page_preview=True,
            disable_notification=False,
            reply_markup=ReplyMarkup(self.buttons())
        )

    def process_update(self, update: Update):
        if not (update and update.callback_query and update.callback_query.data):
            # skip this menu
            return super().process_update(update)
        # end def
        assert update.callback_query.data
        data = json.loads(update.callback_query.data)


    # end def

# end class



class SendButtonMenu(ButtonMenu):
    type = KeyboardButton
    buttons: List[MenuButton]
# end class
