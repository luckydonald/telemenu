#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect_mate
import json
import re
from abc import abstractmethod
from html import escape
from types import LambdaType, BuiltinFunctionType
from typing import Type, Dict, Union, List, ClassVar, Callable, Any, TypeVar, _tp_cache, Pattern, Optional
from pytgbot import Bot
from telestate import TeleMachine, TeleState
from dataclasses import dataclass, field as dataclass_field
from luckydonaldUtils.typing import JSONType
from luckydonaldUtils.logger import logging
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, ReplyMarkup
from .tools import convert_to_underscore

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

    def get_value(cls, key):
        return Menu.get_value(cls, key)
    # end def

    def assertEqual(self, a, b):
        assert a == b
    # end def

    def test_var0(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value('var0'), "(0 normal def)\nPage 123")
    # end def

    def test_var1(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value('var1'), "(1 normal str)\nPage 123")
    # end def

    def test_var2(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value('var2'), "(2 lambda)\nPage 123")
    # end def

    def test_var3(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value('var3'), "(3 classmethod)\nPage 123")
    # end def

    def test_var5(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value('var5'), "(5 classmethod)\nPage 123")
    # end def

    def test_var6(self):
        data = Data()
        data.button_page = 123
        self.assertEqual(self.get_value('var6'), "(6 property)\nPage 123")
    # end def
# end class


_button_id = "CURRENT_STATE.action.<action-type>.<index>;<payload>"  # normal action state
_button_id = "CURRENT_STATE.action.goto.1;"  # normal action state
_button_id = "CURRENT_STATE.page.2"  # pagination

DEFAULT_PLACEHOLDER = object()


class TeleMenuInstancesItem(object):
    """
    This holds a menu and a telestate to register functions to.
    """
    state: TeleState
    machine: 'TeleMenuMachine'
    menu: 'Menu'

    def __init__(self, machine, state, menu):
        self.machine = machine
        self.state = state
        self.menu = menu
    # end def
# end def


class TeleMenuMachine(object):
    instances: Dict[str, TeleMenuInstancesItem]
    states: TeleMachine

    def __init__(self):
        self.instances = {}
        self.states = TeleMachine(__name__)
    # end def

    def register(self, menu_to_register: Type['Menu']) -> Type['Menu']:
        """
        Creates a TeleState for the class and registers the overall menu loading structure..
        Note that the `_id` attribute can be used to overwrite the custom name, that is
        :param menu_to_register: The menu to register
        :return: the class again, unchanged.
        """
        if not issubclass(menu_to_register, Menu):
            raise TypeError(
                f"the parameter menu_to_register should be subclass of {Menu!r}, "
                f"but is type {type(menu_to_register)}: {menu_to_register!r}"
            )
        # end if

        # if menu._id should exist but can be overridden/overwritten by the subclass.
        name = menu_to_register.get_value("_id", data=None)  # parameter data = old name (uppersnake class name)

        if name in self.instances:
            raise ValueError(f'A class with name {name!r} is already registered.')
        # end if
        new_state = TeleState(name=name)
        if hasattr(menu_to_register, 'on_message'):
            pass
        # end if
        self.states.register_state(name, state=new_state)
        instance_item = TeleMenuInstancesItem(
            machine=self, state=new_state, menu=menu_to_register
        )
        self.instances[name] = instance_item
        menu_to_register._state_instance = instance_item
        return menu_to_register
    # end def

    def get_current_menu(self):
        """
        Get the current menu.
        Return `None` if is the `DEFAULT` state, or does not exist in the menu.
        :return:
        """
        state = self.states.CURRENT
        if state == self.states.DEFAULT:
            return None
        # end if
        if state.name not in self.instances:
            return None
        # end if
        return self.instances[state.name]
    # end def
# end class


class MenuData(object):
    message_id: int
    page: int
    data: JSONType

    def __init__(self, message_id: int, page: int = 0, data: JSONType = None):
        self.message_id = message_id
        self.page = page
        self.data = data
    # end def

    def to_json(self):
        return {
            "message_id": self.message_id,
            "page": self.page,
            "data": self.data,
        }
    # end def

    @classmethod
    def from_json(cls, data):
        return cls(
            message_id=data['message_id'],
            page=data['page'],
            data=data['data'],
        )
    # end def
# end class


class Data(object):
    menus: Dict[str, MenuData]  # keys are IDs.
    history: List[str]  # stack of IDs.

    def __init__(self, menus=None, history=None):
        self.menus = {} if menus is None else menus
        self.history = [] if history is None else history
    # end def

    def to_json(self):
        return {
            "menus": self.menus,
            "history": self.history,
        }
        # end def

    @classmethod
    def from_json(cls, data):
        return cls(
            menus={k: MenuData.from_json(v) for k, v in data['menus'].items()},
            history=data['history'],
        )
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
# end class


@dataclass(init=False, eq=False, repr=True)
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
    CALLBACK_PAGINATION_BUTTONS_TYPE = 'pagination'

    _state_instance: TeleMenuInstancesItem
    _id: OptionalClassValueOrCallable[str]

    @classmethod
    def _id(cls, data: None):
        """
        Returns a unique name for this menu.
        Name must be capslock and otherwise only contain numbers and the underscore.

        :return: the name to use
        """
        return convert_to_underscore(cls.__name__).upper()
    # end def

    title: OptionalClassValueOrCallable[str]
    description: OptionalClassValueOrCallable[str]
    done: OptionalClassValueOrCallable[Union['DoneButton', 'Menu']]
    back: OptionalClassValueOrCallable[Union['BackButton', 'Menu']]
    cancel: OptionalClassValueOrCallable[Union['CancelButton', 'Menu']]

    @classmethod
    @abstractmethod
    def get_text(cls, data: Data) -> str:
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
    @abstractmethod
    def get_buttons(cls, data: Data) -> List[InlineKeyboardButton]:
        """
        Retrieval of menu specific buttons.
        This is just a single list of buttons, which will be formatted later.
        Also pagination and back/cancel stuff will be added later as well.

        :param data:
        :return:
        """
        pass
    # end def

    @classmethod
    def get_keyboard(cls, data: Data) -> Union[InlineKeyboardMarkup, ReplyMarkup, None]:
        """
        This is the method which is responsible for returning a ReplyMarkup (e.g. InlineKeyboardMarkup) or None.
        Basically we need to return something which can be used in the `bot.send_message(..., reply_markup=...)` parameter.

        :param data:
        :return:
        """
        buttons = cls.get_buttons(data)

        pages = len(buttons) // 10
        if data.button_page >= pages:
            data.button_page = pages - 1
        # end def
        if data.button_page < 0:
            data.button_page = 0
        # end def

        offset = data.button_page * 10
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
        if data.button_page > 0:
            pagination_buttons.append(InlineKeyboardButton(
                text="<",
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=data.button_page - 1,
                ).to_json_str()
            ))
        # end if
        for i in range(max(data.button_page - 2, 0), data.button_page):
            pagination_buttons.append(InlineKeyboardButton(
                text=str(i),
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=i,
                ).to_json_str()
            ))
        # end def
        for i in range(data.button_page + 1, min(data.button_page + 3, pages)):
            pagination_buttons.append(InlineKeyboardButton(
                text=str(i),
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=i,
                ).to_json_str()
            ))
        # end def
        if data.button_page < pages - 1:
            pagination_buttons.append(InlineKeyboardButton(
                text=">",
                callback_data=CallbackData(
                    type=cls.CALLBACK_PAGINATION_BUTTONS_TYPE,
                    value=data.button_page - 1,
                ).to_json_str()
            ))
        # end if

        return InlineKeyboardMarkup(inline_keyboard=selected_buttons + pagination_buttons)
    # end def

    @classmethod
    def get_done_button(cls, data: Data) -> Union[InlineKeyboardButton, None]:
        done: Union[DoneButton, Menu] = cls.get_value('done')
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
    def get_back_button(cls, data: Data) -> Union[InlineKeyboardButton, None]:
        # TODO implement
        back: Union[BackButton, Menu] = cls.get_value('back')
        assert isinstance(back, BackButton)
        return InlineKeyboardButton(
            text=back.label,
            callback_data=CallbackData(
                type=cls.CALLBACK_DONE_BUTTON_TYPE,
                value=None,
            ).to_json_str(),
        )
    # end def

    @classmethod
    def get_cancel_button(cls, data: Data) -> Union[InlineKeyboardButton, None]:
        # TODO implement
        back: Union[BackButton, Menu] = cls.get_value('back')
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
    def get_value(cls, key, data: Data):
        value = getattr(cls, key, DEFAULT_PLACEHOLDER)
        if value == DEFAULT_PLACEHOLDER:
            raise KeyError(f'Key {key!r} not found.')
        # end if

        # params = dict(state=None, user=None, chat=None)
        params = dict(data=data)
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
    id: Union[str, None] = None  # None means automatic

    @abstractmethod
    def get_label(self, data: Data):
        pass
    # end def

    def get_id(self) -> str:
        return "button@id:" + self.id if hasattr(self, 'id') and self.id else "button@class:" + self.__class__.__name__
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class GotoMenu(Menu):
    MENU_TYPE = 'gotomenu'  # used for CallbackData.type

    menus: ClassValueOrCallableList['GotoButton']

    @classmethod
    def get_buttons(cls, data: Data) -> List[InlineKeyboardButton]:
        return [
            InlineKeyboardButton(
                text=menu.label, callback_data=CallbackData(
                    type=cls.MENU_TYPE,
                    value=menu.menu.get_value('id'),
                ).to_json_str()
            )
            for menu in cls.get_value('menus')
        ]
    # end def

    @classmethod
    def send_message(cls, bot: Bot, chat_id: Union[int, str], data: Data):
        bot.send_message(
            chat_id=chat_id,
            text=cls.get_text(data=data),
            parse_mode='html',
            disable_web_page_preview=True,
            disable_notification=False,
            reply_to_message_id=None,
            reply_markup=cls.get_keyboard(data=data),
        )
    # end def
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


@dataclass
class BackButton(Button):
    label: ClassValueOrCallable[str] = "Back"  # todo: multi-language
    id: Union[str, None] = None
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
    selected: bool

    def __init__(
        self,
        title,
        value: JSONType,
        selected: bool = False
    ):
        self.title = title
        self.value = value
        self.selected = selected
    # end def

    def get_label(self, data: Data):
        return self.STATE_EMOJIS[self.selected] + " " + self.title
    # end def
# end def


@dataclass(init=False, eq=False, repr=True)
class SelectableMenu(Menu):
    MENU_TYPE = 'selectable_menu'  # used for CallbackData.type

    title: str
    value: JSONType
    selected: bool

    def __init__(
        self,
        title,
        value: JSONType,
        selected: bool = False
    ):
        self.title = title
        self.value = value
        self.selected = selected
    # end def

    # noinspection PyShadowingBuiltins
    @classmethod
    def get_our_buttons(cls, data: Data, key='selectable_buttons') -> List[InlineKeyboardButton]:
        """
        Generate InlineKeyboardButton from the buttons.

        Yay, D.R.Y. code.

        :param data: The data, just in case.
        :param key: the name of the class variable containing the list of selectable buttons.
        :return: list of inline buttons
        """
        selectable_buttons: List[Union[SelectableButton, CheckboxButton, RadioButton]] = cls.get_value(key, data)

        buttons: List[InlineKeyboardButton] = []
        for selectable_button in selectable_buttons:
            box = InlineKeyboardButton(
                text=selectable_button.get_label(data=data),
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
    def get_buttons(cls, data: Data) -> List[InlineKeyboardButton]:
        pass
    # end def
# end def


@dataclass(init=False, eq=False, repr=True)
class CheckboxMenu(SelectableMenu):
    MENU_TYPE = 'checkbox'  # used for CallbackData.type

    checkboxes: ClassValueOrCallable['CheckboxButton']

    @classmethod
    def get_buttons(cls, data: Data) -> List[InlineKeyboardButton]:
        return cls.get_our_buttons(data, 'checkboxes')
    # end def
# end class


class CheckboxButton(SelectableButton):
    STATE_EMOJIS = {True: "✅", False: "❌"}
# end class


@dataclass(init=False, eq=False, repr=True)
class RadioMenu(SelectableMenu):
    MENU_TYPE = 'radiobutton'  # used for CallbackData.type

    radiobuttons: ClassValueOrCallable['RadioButton']

    @classmethod
    def get_buttons(cls, data: Data) -> List[InlineKeyboardButton]:
        return cls.get_our_buttons(data, 'radiobuttons')
    # end def
# end class


class RadioButton(SelectableButton):
    STATE_EMOJIS = {True: "🔘", False: "⚫️"}
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
    def get_buttons(cls, data: Data) -> List[InlineKeyboardButton]:
        return []
    # end def

    @classmethod
    def get_keyboard(cls, data: Data) -> ForceReply:
        """
        We always return a force reply, as we don't do menu now, but just wanna have text/files/media/...
        :param data:
        :return:
        """
        return ForceReply(selective=True)
    # end def

    @classmethod
    def get_text(cls, data: Data) -> str:
        """
        This is lacking translations, so you might have to overwrite it with your own texts...
        :param data:
        :return:
        """
        text = super().get_text(data)
        return (
            text + "\n\n" +
            cls.TEXTUAL_BUTTON_TEXT_ALTERNATIVE[cls.get_back_button(data) is not None]
        )
    # end def
# end def


@dataclass(init=False, eq=False, repr=True)
class TextMenu(SendMenu):
    """
    Simple reply text to this menu.
    Uses force reply.
    """
    MENU_TYPE = 'text'  # used for CallbackData.type


    @classmethod
    @abstractmethod
    def _parse(cls, data: Data, text: str) -> JSONType:
        raise NotImplementedError('Subclasses must implement that.')
    # end def

    @classmethod
    def on_update(cls, update, message):
        text = message
        pass
    # end def

# end class


@dataclass(init=False, eq=False, repr=True)
class TextStrMenu(TextMenu):
    """
    A force reply text string.
    """
    MENU_TYPE = 'text_str'  # used for CallbackData.type

    @classmethod
    def _parse(cls, data: Data, text: str) -> JSONType:
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
    def _parse(cls, data: Data, text: str) -> JSONType:
        return int(text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextFloatMenu(TextMenu):
    """
    A force reply text string parsed as float.
    """
    MENU_TYPE = 'text_float'  # used for CallbackData.type

    def _parse(self, data: Data, text: str) -> float:
        return float(text)
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextPasswordMenu(TextMenu):
    """
    A force reply text string which deletes your answer again.
    """
    MENU_TYPE = 'text_password'  # used for CallbackData.type
    def _parse(self, data: Data, text: str) -> str:
        return text
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class TextEmailMenu(TextMenu):
    """
    A force reply text string which is validated as valid email.
    """
    MENU_TYPE = 'text_email'  # used for CallbackData.type

    def _parse(self, data: Data, text: str) -> str:
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
    MENU_TYPE = 'text_upload'  # used for CallbackData.type

    allowed_mime_types: Union[List[Union[str, Pattern]], None] = None
    allowed_extensions: Union[List[str], None] = None
# end def


# ------------------------------
# TEST CLASSES
# here the stuff is implemented
# ------------------------------


telemenu = TeleMenuMachine()


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

    # noinspection PyMethodMayBeStatic
    def checkboxes(self) -> List[CheckboxButton]:
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
            RadioButton(title="Rainbow Dash", selected=False, value='rd'),
            RadioButton(title="Littlepip", selected=True, value='waifu'),
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

    done = DoneButton(menu=TestTextPasswordMenu),
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

    done = DoneButton(menu=TestTextPasswordMenu)
# end class
