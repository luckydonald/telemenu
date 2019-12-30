#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
from abc import abstractmethod
from dataclasses import dataclass, field as dataclass_field
from html import escape
from types import LambdaType, BuiltinFunctionType
from typing import ClassVar, Union, Type, cast, Callable, Any, List, Dict, Pattern, Tuple

from luckydonaldUtils.decorators import classproperty
from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

from luckydonaldUtils.typing import JSONType
from pytgbot import Bot
from pytgbot.api_types.receivable.updates import Message, Update
from pytgbot.api_types.sendable.reply_markup import ReplyMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from pytgbot.api_types.sendable.reply_markup import ReplyKeyboardMarkup, ReplyKeyboardRemove
from teleflask import TBlueprint
from teleflask.exceptions import AbortProcessingPlease

from . import ClassValueOrCallable, OptionalClassValueOrCallable, ClassValueOrCallableList
from .data import Data, MenuData, CallbackData
from .utils import convert_to_underscore
from .machine import TeleMenuMachine, TeleMenuInstancesItem, TeleStateMachineMenuSerialisationAdapter
from .inspect_mate_keyless import is_class_method, is_regular_method, is_static_method, is_property_method
from telestate import TeleStateMachine, TeleState

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


DEFAULT_PLACEHOLDER = object()


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
    MENU_TYPE = 'menu'  # used for CallbackData.type
    CALLBACK_DONE_BUTTON_TYPE = 'done'
    CALLBACK_BACK_BUTTON_TYPE = 'back'
    CALLBACK_PAGINATION_BUTTONS_TYPE = 'pagination'

    _state_instance: ClassVar[Union[TeleMenuInstancesItem, TeleMenuInstancesItem]]

    # noinspection PyMethodParameters
    @classproperty
    def data(cls: Type['Menu']) -> Union[Data, None]:
        if cls._state_instance is None:
            # we're called by the @dataclasses class inspector
            return None
        # end if
        return cls._state_instance.state.data
    # end def
    data: ClassVar[Data]
    data: Data

    @classproperty
    def menu_data(cls: Type['Menu']) -> Union[MenuData, None]:
        if cls.data is None:
            return None
        if cls.id not in cls.data.menus:
            return None
        # end if
        return cls.data.menus[cls.id]
    # end def

    # noinspection PyPropertyDefinition,PyMethodParameters
    @data.setter
    def data(cls: Type['Menu'], data: Union[Data, None]):
        cls.store_data(data)
    # end def

    @classmethod
    def store_data(cls: Type['Menu'], data: Union[Data, None]):
        assert isinstance(data, Data) or data is None
        cls._state_instance.state.data = data
    # end def

    bot: ClassVar[Bot]
    # noinspection PyMethodParameters
    @classproperty
    def bot(cls: Type['Menu']) -> Union[Bot, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TBlueprint, cls.tblueprint).bot
    # end def

    menu_machine: ClassVar[TBlueprint]
    # noinspection PyMethodParameters
    @classproperty
    def menu_machine(cls: Type['Menu']) -> Union[TeleMenuMachine, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleMenuMachine, cls._state_instance.machine)
    # end def

    state_machine: ClassVar[TBlueprint]
    # noinspection PyMethodParameters
    @classproperty
    def state_machine(cls: Type['Menu']) -> Union[TeleStateMachine, TeleStateMachineMenuSerialisationAdapter, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleMenuMachine, cls.menu_machine).states
    # end def

    tblueprint: ClassVar[TBlueprint]
    # noinspection PyMethodParameters
    @classproperty
    def tblueprint(cls: Type['Menu']) -> Union[TBlueprint, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleStateMachine, cls.state_machine).blueprint
    # end def

    # noinspection PyMethodParameters
    @classproperty
    def id(cls: Type['Menu']) -> str:
        """
        Returns a unique name for this menu.
        Name must be capslock and otherwise only contain numbers and the underscore.

        :return: the name to use
        """
        return convert_to_underscore(cls.__name__).upper()
    # end def

    # noinspection PyMethodParameters
    @classmethod
    def get_last_menu(cls, activate=False) -> Union[None, Type['Menu']]:
        """
        Returns the previous menu in the history, or None if there is none.
        :return:
        """
        return cls._state_instance.machine.get_last_menu(activate=activate)
    # end def

    @classmethod
    def _activate(cls, add_history_entry: Union[bool, None] = None):
        """
        Activates the underlying state of the menu, and copies over the data to the new state.

        :param add_history_entry: If we should add to the menu history.
                                  `None` (default): Automatically add the new menu to the history, if that's not the active menu already.
                                  `True`: Forcefully add the menu to the history, even if we are activating the menu we're already are on.
                                  `False`: Don't append to the history.
        :type  add_history_entry: bool|None
        :return:
        """
        instance: TeleMenuInstancesItem = cls._state_instance
        data = cls._state_instance.machine.states.CURRENT.data
        if data is None:
            data = Data()
        # end if
        if add_history_entry is None:
            # None: Add history automatically, if we're not the active menu already, especially if the list is empty.
            add_history_entry = len(data.history) == 0 or data.history[-1] != cls.id
        # end if
        if add_history_entry:
            data.history.append(cls.id)
        # end if
        if cls.id not in data.menus:
            data.menus[cls.id] = MenuData()
        # end if
        instance.state.activate(data)
    # end def

    @classmethod
    def activate(cls, add_history_entry: Union[bool, None] = None):
        """
        Activates the underlying state of the menu, and copies over the data to the new state.

        :param add_history_entry: If we should add to the menu history.
                                  `None` (default): Automatically add the new menu to the history, if that's not the active menu already.
                                  `True`: Forcefully add the menu to the history, even if we are activating the menu we're already are on.
                                  `False`: Don't append to the history.
        :type  add_history_entry: bool|None
        :return:
        """
        cls._activate(add_history_entry=add_history_entry)
    # end def

    @classmethod
    def show(cls):
        """
        Activates the menu, and returns a sendable update.
        :return:
        """
        cls._activate()
    # end def

    @classmethod
    def get_value_by_name(cls, key):
        """
        This function is able to grab any value from a menu class by property name,
        no matter if it is a string or (class-/instance-/lambda-/...) function.
        Also it will provide the `data` to that function as well.
        In case of native strings, str.format(data=data) is called as well.

        :param key:
        :return:
        """
        value = getattr(cls, key, DEFAULT_PLACEHOLDER)
        if value == DEFAULT_PLACEHOLDER:
            raise KeyError(f'Key {key!r} not found.')
        # end if
        return cls.get_value(value)
    # end def

    @classmethod
    def get_value(cls, value: Union[Callable, LambdaType, str, property, JSONType, Any]) -> Any:
        """
        This function is able to grab any value from a menu class by property name,
        no matter if it is a string or (class-/instance-/lambda-/...) function.
        Also it will provide the `data` to that function as well.
        In case of native strings, str.format(data=data) is called as well.

        :param value: The variable to resolve.
        :return:
        """

        # params = dict(state=None, user=None, chat=None)
        if isinstance(value, str):
            return value.format(data=cls.data)
        # end if
        if isinstance(value, BuiltinFunctionType):
            # let's assume you wrote `some_var = "...".format`
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # some_var = some_function()
                return value(data=cls.data)
            elif len(sig.parameters) > 0:
                # some_var = some_function(data)
                return value(cls.data)
            # end if
            # some_var = some_function()
            return value()
        # end if
        if is_class_method(value):
            value: Callable
            # @classmethod
            # def some_func(cls, data)
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # some_var = some_function(data=None)
                first_param: inspect.Parameter = list(sig.parameters.values())[0]
                if 'cls' in sig.parameters or isinstance(first_param.annotation, type) and issubclass(first_param.annotation, Menu):
                    return value(data=cls.data)  # value already is class.some_function, therefore cls will be filled.
                return value(data=cls.data)
            elif len(sig.parameters) == 1:
                # some_var = some_function(data)
                return value(cls.data)
            # end if
            # some_var = some_function()
            return value()
            # end if
        if is_regular_method(value):
            # def some_func(self, ...)
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # def some_func(self, data)
                return value(self=cls, data=cls.data)
                # end if
            return value(self=cls)
        # end if
        if is_static_method(value):
            # @staticmethod
            # def some_func(...):
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                # def some_func(data)
                return value(data=cls.data)
            # end if
            return value()
        # end if
        if is_property_method(value):
            # @property
            # def some_func(self):
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                return value.fget(data=cls.data)
            # end if
            return value.fget()
        # end if
        if isinstance(value, LambdaType):
            sig = inspect.signature(value)
            if 'data' in sig.parameters:
                return value(data=cls.data)
            # end if
            return value()
        # end if

        # if all that didn't work, just return it.
        return value
    # end def

    @classmethod
    def register_state_instance(cls, instance_item):
        """
        Function to register a state.

        :param instance_item:
        :return:
        """
        cls._state_instance = instance_item
    # end def

    title: OptionalClassValueOrCallable[str]
    description: OptionalClassValueOrCallable[str]
    done: OptionalClassValueOrCallable[Union['DoneButton', 'Menu', 'GotoButton']]
    back: OptionalClassValueOrCallable[Union['BackButton', 'Menu', 'GotoButton']]
    cancel: OptionalClassValueOrCallable[Union['CancelButton', 'Menu', 'GotoButton']]

    @classmethod
    def text(cls) -> str:
        """
        This function returns the HTML formatted text for the button.
        :return:
        """
        text = ""
        title = cls.get_value_by_name('title')
        if title:
            text += f"<b>{escape(title)}</b>\n"
        # end if
        description = cls.get_value_by_name('description')
        if description:
            text += f"{escape(description)}\n"
        # end if
        # text += f"<i>Selected: {escape(description)}</i>\n"
        return text
    # end def

    @classmethod
    @abstractmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        """
        This funktion is responsible for returning the `reply_markup` parameter,
        as used in pytgbot.Bot.send_message and other send_* methods.
        """
        pass
    # end def

    @classmethod
    #@abstractmethod
    def send(cls) -> Message:
        """
        This function sends a message to the state's chat and stores the information about it in the current update.

        :return:
        """
        bot: Bot = cast(Bot, cls.bot)
        assert_type_or_raise(bot, Bot, parameter_name='bot')

        text: str
        text = cls.get_value(cls.text)

        reply_markup: Union[None, ReplyMarkup, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        reply_markup = cls.get_value(cls.reply_markup)

        update: Update
        update = cast(TeleState, cast(TeleStateMachine, cls._state_instance.machine).states.CURRENT).update

        chat_id: Union[int, None]
        user_id: Union[int, None]
        chat_id, user_id = TeleStateMachine.msg_get_chat_and_user(update)

        reply_chat: Union[int, None]
        reply_msg: Union[int, None]
        reply_chat, reply_msg = TeleStateMachine.msg_get_reply_params(update)
        assert_type_or_raise(chat_id, int, parameter_name='chat_id')

        msg = bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='html',
            disable_web_page_preview=True,
            disable_notification=False,
            reply_to_message_id=reply_msg,
            reply_markup=reply_markup,
        )
        # If a new message is to be posted, the new message_id must be tracked.
        cast(MenuData, cls.menu_data).message_id = msg.message_id
        return msg
    # end def

    @classmethod
    def refresh(cls, done: bool = False) -> Message:
        """
        Edit the posted message to reflect new state, or post a new one if needed.
        To find the message to edit it uses the last saved state message_id as be found in `menu.data.menus[menu.id].message_id`.

        # TODO: If a new message is to be posted newly, the new message_id must be tracked,
        # TODO: and maybe also the old keyboard removed.
        # TODO: maybe menus should offer a 'def done_text_addendum(cls) -> str' function for `done=True`.

        :param done: Set to true if this message is not the current any longer.
                     Used to e.g. include the selection in the message when the new menu is opened below.
        :return:
        """
        bot: Bot = cast(Bot, cls.bot)
        assert_type_or_raise(bot, Bot, parameter_name='bot')

        text: str
        text = cls.get_value(cls.text)

        reply_markup: Union[None, ReplyMarkup, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply]
        reply_markup = cls.get_value(cls.reply_markup) if not done else None

        message_id: int
        message_id = cast(MenuData, cls.menu_data).message_id

        update: Update
        update = cast(TeleStateMachine, cls._state_instance.machine).states.CURRENT.update

        chat_id: Union[int, None]
        user_id: Union[int, None]
        chat_id, user_id = TeleStateMachine.msg_get_chat_and_user(update)
        assert_type_or_raise(chat_id, int, parameter_name='chat_id')

        # reply_chat, reply_msg = TeleStateMachine.msg_get_reply_params(update)

        msg = bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='html',
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
        return msg
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class ButtonMenu(Menu):
    """
    Subclass for everything with inline Keyboard
    """

    @classmethod
    @TeleMenuMachine.registerer.on_update('callback_query')
    def on_callback_query(cls, update: Update):
        """
        Handles callbackdata, registered by
        :param update:
        :return:
        """
        # Update.callback_query
        # CallbackData(
        #     type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
        #     value=data.page - 1,
        # ).to_json_str(),

        data = CallbackData.from_json_str(update.callback_query.data)
        try:
            return cls.process_callback_data(data)
        except AbortProcessingPlease as e:
            return e.return_value
        # end try
    # end def

    @classmethod
    def process_callback_data(cls, data: CallbackData):
        # check if we need to do pagination
        if data.type == cls.CALLBACK_PAGINATION_BUTTONS_TYPE:
            assert isinstance(cls.menu_data, MenuData)
            cls.menu_data.page += 1
            cls.refresh(done=False)
            raise AbortProcessingPlease()  # basically a subclass callstack safe "return None"
        # end if
    # end def

    @classmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        """
        Generate an inline markup for the message to contain.
        :return:
        """
        return cls.get_keyboard()
    # end def

    @classmethod
    @abstractmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        """
        Retrieval of menu specific buttons.
        This is just a single list of buttons, which will be formatted later.
        Also pagination and back/cancel stuff will be added later as well.

        :return:
        """
        pass
    # end def

    @classmethod
    def get_keyboard(cls) -> Union[InlineKeyboardMarkup, ReplyMarkup, None]:
        """
        This is the method which is responsible for returning a ReplyMarkup (e.g. InlineKeyboardMarkup) or None.
        Basically we need to return something which can be used in the `bot.send_message(..., reply_markup=...)` parameter.

        :return:
        """
        buttons = cls.get_buttons()

        pages = (len(buttons) // 10) + 1
        data: MenuData = cls.menu_data
        if data.page >= pages:
            data.page = pages - 1
        # end def
        if data.page < 0:
            data.page = 0
        # end def

        offset = data.page * 10
        selected_buttons = buttons[offset: offset + 10]

        keyboard = []
        for i in range(len(selected_buttons)):
            # we iterate through the buttons and split them into left and right.
            if i % 2 == 0:  # left button, and first of row
                keyboard.append([])
            # end if
            keyboard[-1].append(selected_buttons[i])
        # end if

        pagination_buttons = []
        if data.page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="<",
                    callback_data=CallbackData(
                        type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                        value=data.page - 1,
                    ).to_json_str(),
                )
            )
        # end if
        for i in range(max(data.page - 2, 0), data.page):
            pagination_buttons.append(InlineKeyboardButton(
                text=str(i),
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=i,
                ).to_json_str()
            ))
        # end def
        for i in range(data.page + 1, min(data.page + 3, pages)):
            pagination_buttons.append(InlineKeyboardButton(
                text=str(i),
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=i,
                ).to_json_str()
            ))
        # end def
        if data.page < pages - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text=">",
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=data.page - 1,
                ).to_json_str()
            ))
        # end if

        button_rows = []
        for i, button in enumerate(selected_buttons + pagination_buttons):
            if i % 2 == 0:
                button_rows.append([])  # add list
            # end if
            button_rows[-1].append(button)
        # end for

        return InlineKeyboardMarkup(inline_keyboard=button_rows)
    # end def

    @classmethod
    def get_done_button(cls) -> Union[InlineKeyboardButton, None]:
        from .buttons import DoneButton
        done: Union[DoneButton, Menu] = cls.get_value_by_name('done')
        if isinstance(done, DoneButton):
            return InlineKeyboardButton(
                text=done.label,
                callback_data=CallbackData(
                    type=cls.CALLBACK_DONE_BUTTON_TYPE,
                    value=None,
                ).to_json_str(),
            )
        elif isinstance(done, Menu):
            return InlineKeyboardButton(
                text=done.title,
                callback_data=CallbackData(
                    type=cls.CALLBACK_DONE_BUTTON_TYPE,
                    value=None,
                ).to_json_str(),
            )
        # end if
    # end def

    @classmethod
    def get_back_button(cls) -> Union[InlineKeyboardButton, None]:
        # TODO implement
        from .buttons import GotoButton, BackButton

        last_menu = cls.get_last_menu()
        assert isinstance(last_menu, BackButton)
        return InlineKeyboardButton(
            text=last_menu.label,
            callback_data=CallbackData(
                type=cls.CALLBACK_DONE_BUTTON_TYPE,
                value=None,
            ).to_json_str(),
        )
    # end def

    @classmethod
    def get_cancel_button(cls) -> Union[InlineKeyboardButton, None]:
        # TODO implement
        from .buttons import GotoButton, BackButton, CancelButton

        back: Union[BackButton, Type[Menu]] = cls.get_value_by_name('back')
        assert isinstance(back, CancelButton)
        return InlineKeyboardButton(
            text=back.label,
            callback_data=CallbackData(
                type=cls.CALLBACK_DONE_BUTTON_TYPE,
                value=None,
            ).to_json_str(),
        )

    # end def

    @classmethod
    def get_own_buttons(cls) -> List[InlineKeyboardButton]:
        return []
    # end def

    @classmethod
    @abstractmethod
    def on_inline_query(cls, update: Update):
        """
        Processes the inline_query update, to do the button clicky thingy.

        :param update:
        :return:
        """
        pass
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class GotoMenu(ButtonMenu):
    MENU_TYPE = 'gotomenu'  # used for CallbackData.type

    menus: ClassValueOrCallableList[Union['GotoButton', Type['Menu']]]

    @classmethod
    @abstractmethod
    def menus(cls) -> List['GotoButton', Type['Menu']]:
        pass
    # end def

    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        from .buttons import GotoButton
        return [
            InlineKeyboardButton(
                text=menu.label, callback_data=CallbackData(
                    type=cls.MENU_TYPE,
                    value=menu.menu.id if isinstance(menu, GotoButton) else menu.id,
                ).to_json_str()
            )
            for menu in cls.get_value_by_name('menus')
        ]
    # end def

    @classmethod
    def process_callback_data(cls, data: CallbackData):
        if data.type == cls.MENU_TYPE:
            menu_id = data.value
            menu: Menu = cls._state_instance.machine.instances[menu_id]
            cls.refresh(done=False)
            menu.activate()
            menu.send()
            raise AbortProcessingPlease()
        # end if
        super().process_callback_data(data)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class SelectableMenu(ButtonMenu):
    """
    Menu for the option to choose one from many.
    """
    MENU_TYPE = 'selectable_menu'  # used for CallbackData.type

    title: str

    # noinspection PyShadowingBuiltins
    @classmethod
    def get_our_buttons(cls, key='selectable_buttons') -> List[InlineKeyboardButton]:
        """
        Generate InlineKeyboardButton from the buttons.

        Yay, D.R.Y. code.

        :param key: the name of the class variable containing the list of selectable buttons.
        :return: list of inline buttons
        """
        from .buttons import GotoButton, SelectableButton, CheckboxButton, RadioButton

        selectable_buttons: List[
            Union[
                SelectableButton,
                CheckboxButton,
                RadioButton
            ]
        ] = cls.get_value_by_name(key)

        buttons: List[InlineKeyboardButton] = []
        for selectable_button in selectable_buttons:
            box = InlineKeyboardButton(
                text=selectable_button.get_label(menu_data=cls.menu_data),
                callback_data=CallbackData(
                    type=cls.MENU_TYPE,
                    value=selectable_button.value,
                ).to_json_str()
            )
            buttons.append(box)
        # end for
        return buttons
    # end def

    @classmethod
    @abstractmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        pass
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class CheckboxMenu(SelectableMenu):
    MENU_TYPE = 'checkbox'  # used for CallbackData.type
    DATA_TYPE = Dict[str, bool]  # key is

    checkboxes: ClassValueOrCallable['CheckboxButton']

    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        return cls.get_our_buttons(key='checkboxes')
    # end def

    @classmethod
    def on_inline_query(cls, update: Update):
        """
        Processes the inline_query update, to do the button clicky thingy.

        :param update:
        :return:
        """
        button = update.callback_query.data
        cast(MenuData, cls.menu_data).data[button] = not cast(MenuData, cls.menu_data).data[button]  # toggle the button.
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class RadioMenu(SelectableMenu):
    MENU_TYPE = 'radiobutton'  # used for CallbackData.type
    DATA_TYPE = str

    radiobuttons: ClassValueOrCallable['RadioButton']
    data: str

    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        return cls.get_our_buttons(key='radiobuttons')
    # end def

    @classmethod
    def on_inline_query(cls, update: Update):
        """
        Processes the inline_query update, to do the button clicky thingy.

        :param update:
        :return:
        """
        button = update.callback_query.data
        cls.data = button
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class SendMenu(Menu):
    """
    Superclass for all things which don't really have buttons, but instead needs something sent.
    """

    MENU_TYPE = 'send'
    TEXTUAL_BUTTON_TEXT_ALTERNATIVE = {  # True: has back button.
        True: "You can click /back to go back to the last menu or press /cancel to abort the whole process.",
        False: "You can press /cancel to abort the whole process."
    }

    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
        return []
    # end def

    @classmethod
    def get_keyboard(cls) -> ForceReply:
        """
        We always return a force reply, as we don't do menu now, but just wanna have text/files/media/...
        :return:
        """
        return ForceReply(selective=True)
    # end def

    @classmethod
    def text(cls) -> str:
        """
        This is lacking translations, so you might have to overwrite it with your own texts...
        :return:
        """
        text = cls.get_value(super().text)
        return (
            text + "\n\n" +
            cls.TEXTUAL_BUTTON_TEXT_ALTERNATIVE[cls.get_back_button() is not None]
        )
    # end def

    @classmethod
    def get_back_button(cls) -> Union[None, 'telemenu.buttons.BackButton']:
        pass
    # end def

    @classmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        return ForceReply(selective=True)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextMenu(SendMenu):
    """
    Simple reply text to this menu.
    Uses force reply.
    """
    MENU_TYPE = 'text'  # used for CallbackData.type

    @classmethod
    @abstractmethod
    def _parse(cls, text: str) -> JSONType:
        raise NotImplementedError('Subclasses must implement that.')
    # end def

    # noinspection PyUnusedLocal
    @classmethod
    @TeleMenuMachine.registerer.on_message('text')
    def on_message_listener(cls, update: Update, msg: Message):
        logger.debug(f'TextMenu ({cls.__name__}) got text update: {msg.text!r}')
        return cls._parse(msg.text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextStrMenu(TextMenu):
    """
    A force reply text string.
    """
    MENU_TYPE = 'text_str'  # used for CallbackData.type

    @classmethod
    def _parse(cls, text: str) -> JSONType:
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextIntMenu(TextMenu):
    """
    A force reply text string parsed as integer.
    """
    MENU_TYPE = 'text_int'  # used for CallbackData.type

    @classmethod
    def _parse(cls, text: str) -> JSONType:
        return int(text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextFloatMenu(TextMenu):
    """
    A force reply text string parsed as float.
    """
    MENU_TYPE = 'text_float'  # used for CallbackData.type

    def _parse(self, text: str) -> float:
        return float(text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextPasswordMenu(TextMenu):
    """
    A force reply text string which deletes your answer again.
    """
    MENU_TYPE = 'text_password'  # used for CallbackData.type
    def _parse(self, text: str) -> str:
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextEmailMenu(TextMenu):
    """
    A force reply text string which is validated as valid email.
    """
    MENU_TYPE = 'text_email'  # used for CallbackData.type

    def _parse(self, text: str) -> str:
        if "@" not in text or "." not in text:  # TODO: improve validation.
            raise ValueError('No good email.')
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextTelMenu(TextMenu):
    """
    A force reply text string which is validated as valid telephone number.
    """
    MENU_TYPE = 'text_tel'  # used for CallbackData.type

    def _parse(self, text: str) -> str:
        # TODO: add validation.
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextUrlMenu(TextMenu):
    """
    A force reply text string which is validated as valid url.
    """
    MENU_TYPE = 'text_url'  # used for CallbackData.type

    allowed_protocols: List[str] = dataclass_field(default_factory=lambda: ['http', 'https'])

    def _parse(self, text: str) -> str:
        if not any(text.startswith(protocol) for protocol in self.allowed_protocols):
            raise ValueError('Protocol not allowed')
        # end if
        # TODO: improve validation.
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class UploadMenu(SendMenu):
    """
    A force reply file upload.
    """
    MENU_TYPE = 'upload_file'  # used for CallbackData.type
    UPDATE_ATTRIBUTE = 'document'

    allowed_mime_types: Union[List[Union[str, Pattern]], None] = None
    allowed_extensions: Union[List[str], None] = None

    @classmethod
    @TeleMenuMachine.registerer.on_message
    def on_message_listener(cls, update: Update, msg: Message):
        from pytgbot.api_types.receivable.media import PhotoSize
        if not hasattr(msg, cls.UPDATE_ATTRIBUTE):
            return None
        # end if
        file_attr = getattr(msg, cls.UPDATE_ATTRIBUTE)  # something like msg.document, msg.photo, ...
        if hasattr(file_attr, 'file_id'):  # Document, Video, Gif, Sticker, ...
            file_id = file_attr.file_id
        elif isinstance(file_attr, list):
            biggest_size = 0
            biggest_file = None
            for photo in file_attr:
                assert isinstance(photo, PhotoSize)
                if photo.file_size > biggest_size:
                    biggest_file = photo.file_id
                    biggest_size = photo.file_size
                # end if
            # end for
            file_id = biggest_file
        else:
            raise ValueError(f'Don\'t know how to handle `Message.{cls.UPDATE_ATTRIBUTE}`...')
        # end if

        return file_id
    # end def
# end class
