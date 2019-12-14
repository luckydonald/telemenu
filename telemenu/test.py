#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
import unittest

import json
import re
from abc import abstractmethod
from html import escape
from types import LambdaType, BuiltinFunctionType
from typing import Type, Dict, Union, List, ClassVar, Callable, Any, TypeVar, Pattern, cast, Tuple, Generator
from pytgbot import Bot
from teleflask import TBlueprint
from telestate import TeleMachine, TeleState
from dataclasses import dataclass, field as dataclass_field
from teleflask.exceptions import AbortProcessingPlease
from luckydonaldUtils.typing import JSONType
from luckydonaldUtils.logger import logging
from telestate.contrib.simple import TeleMachineSimpleDict
from luckydonaldUtils.decorators import classproperty
from luckydonaldUtils.exceptions import assert_type_or_raise
from pytgbot.api_types.receivable.updates import Update, Message
from pytgbot.api_types.sendable.reply_markup import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply, ReplyMarkup
from .utils import convert_to_underscore
from .inspect_mate_keyless import is_class_method, is_regular_method, is_static_method, is_property_method

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


# TODO: rewrite (de)serialize logic/extendability in the Telemachine class to be separate form the database driver.
# TODO: maybe the drivers should be separate instead, and it's like `telemachine = Telemachine(driver=SimpleDictDBDriver).
class TeleMenuStateMachine(TeleMachineSimpleDict):
    """
    Normal TeleStateMachine, but with custom (de)serialisation methods,
    directly converting it to and from the `Data` type.
    """
    @staticmethod
    def deserialize(state_name, db_data):
        array: Union[Dict[str, JSONType], None] = super().deserialize(state_name, db_data)
        if array is None:
            return Data(menus={}, history=[])
        # end if
        return Data.from_dict(array)
    # end def

    @staticmethod
    def serialize(state_name, state_data: 'Data'):
        data = state_data.to_dict()
        return super().serialize(state_name, data)
    # end def
# end class


class registerer(object):
    """
    Mark functions to be included in the menu's state's tblueprint,
    as soon as that is assigned.

    Basically first the decorators next to the functions in the class are executed,
    and a marker is set.
    `function._tmenu_mark_ = registerer.StoreMark(...)`

    Later this can be retrieved with `registerer.collect_marked_functions(cls)`.
    In our case that is called by `@telemenu.register` where `telemenu = TelemenuMachine(...)`.

    Basically a complicated version of https://stackoverflow.com/a/2367605/3423324.
    """
    class StoredMark(object):
        MARK = '_tmenu_mark_'

        marked_function: Callable
        register_function: str
        register_args: Tuple
        register_kwargs: Dict[str, Any]
        register_name: Union[str, None]

        def __init__(
            self,
            marked_function: Callable,
            register_function: str,
            register_args: Tuple,
            register_kwargs: Dict[str, Any]
        ):
            self.marked_function = marked_function
            self.register_function = register_function
            self.register_args = register_args
            self.register_kwargs = register_kwargs
            self.register_name = None
        # end def

        def __repr__(self) -> str:
            return (
                f'{self.__class__.__name__}('
                f'marked_function={self.marked_function!r}, '
                f'register_function={self.register_function!r}, '
                f'register_args={self.register_args!r}, '
                f'register_kwargs={self.register_kwargs!r}, '
                f'register_name={self.register_name!r}'
                f')'
            )
        # end def
    # end class

    @classmethod
    def _mark_function(cls, menu_function, register_function, *args, **kwargs):
        setattr(
            menu_function,
            registerer.StoredMark.MARK,
            cls.StoredMark(
                marked_function=menu_function,
                register_function=register_function,
                register_args=args, register_kwargs=kwargs,
            )
        )
    # end def

    @classmethod
    def collect_marked_functions_iter(cls, menu: Type['Menu']) -> Generator['StoredMark', None, None]:
        """
        Method generating yielding a list of all previously marked functions.
        :param menu: The menu we want to collect the @registerer.* stuff on.
        :return:
        """
        for name, method in inspect.getmembers(menu, inspect.isroutine):
            if not hasattr(method, registerer.StoredMark.MARK):  # this might wake it up.
                method = getattr(menu, name)
            # end if
            if hasattr(method, registerer.StoredMark.MARK):
                mark: cls.StoredMark = getattr(method, registerer.StoredMark.MARK)
                mark.register_name = name
                yield mark
            # end if
        # end for
    # end def

    @classmethod
    def collect_marked_functions(cls, menu: Type['Menu']) -> List['StoredMark']:
        """
        Method generating returning a list of all previously marked functions.
        :param menu: The menu we want to collect the @registerer.* stuff on.
        :return:
        """
        return list(cls.collect_marked_functions_iter(menu))
    # end def

    @staticmethod
    def _build_listener(register_function):
        def decorator_function(*required_keywords: Tuple[str]) -> Union[Callable,  Callable[[Callable], Callable]]:
            """
            Like `BotCommandsMixin.on_message`, but for a static `Menu`.
            """
            def actual_wrapping_method(function:  Callable):
                registerer._mark_function(function, register_function, *required_keywords)
                return function
            # end def
            if (
                len(required_keywords) == 1 and  # given could be the function, or a single required_keyword.
                not isinstance(required_keywords[0], str) # not string -> must be function
             ):
                # -> plain function, no strings
                # @on_message
                found_function = required_keywords[0]
                required_keywords = tuple()  # we call the wrapper ourself, but remove the function from `required_keywords`
                return actual_wrapping_method(function=found_function)  # not string -> must be function
            # end if
            # -> else: *required_keywords are the strings
            # @on_message("text", "sticker", "whatever")
            return actual_wrapping_method  # let that function be called again with the function.
        # end def
        return decorator_function
    # end def

    on_message: Union[Callable[[Callable], Callable], Callable[..., Callable[[Callable], Callable]]]
    on_command: Union[Callable[[Callable], Callable], Callable[..., Callable[[Callable], Callable]]]
    on_update: Union[Callable[[Callable], Callable], Callable[..., Callable[[Callable], Callable]]]

    @classmethod
    def on_update(cls, *args: str):
        pass
    # pass
# end def


# noinspection PyTypeHints
registerer.on_message: Callable[[], Callable] = staticmethod(getattr(registerer, '_build_listener')('on_message'))
# noinspection PyTypeHints
registerer.on_command: Callable = staticmethod(getattr(registerer, '_build_listener')('on_command'))
# noinspection PyTypeHints
registerer.on_update: Callable = staticmethod(getattr(registerer, '_build_listener')('on_update'))


@dataclass(init=False, repr=True)
class TeleMenuMachine(object):
    instances: Dict[str, TeleMenuInstancesItem]
    states: TeleMenuStateMachine

    def __init__(self, states: TeleMenuStateMachine = None, teleflask_or_tblueprint=None):
        assert_type_or_raise(states, TeleMenuStateMachine, None, parameter_name='states')
        self.instances = {}
        self.states = states
        if not self.states:
            self.states = TeleMenuStateMachine(__name__, teleflask_or_tblueprint)
        # end def
    # end def

    registerer = registerer

    def register(self, menu_to_register: Type['Menu']) -> Type['Menu']:
        """
        Creates a TeleState for the class and registers the overall menu loading structure..
        Note that the `id` attribute can be used to overwrite the custom name with a different function.
        :param menu_to_register: The menu to register
        :return: the class again, unchanged.
        """
        if not issubclass(menu_to_register, Menu):
            raise TypeError(
                f"the parameter menu_to_register should be subclass of {Menu!r}, "
                f"but is type {type(menu_to_register)}: {menu_to_register!r}"
            )
        # end if

        # def menu.id can be overridden by the subclass.
        name = menu_to_register.id  # parameter data = old name (uppersnake class name)
        if name in self.instances:
            raise ValueError(f'A class with name {name!r} is already registered.')
        # end if
        new_state = TeleState(name=name)

        # register all marked function
        mark: registerer.StoredMark
        for mark in registerer.collect_marked_functions_iter(menu_to_register):
            # collect the correct telestate/tblueprint register function.
            logger.debug(f'found mark: {mark!r}')
            register_function: Callable = getattr(new_state, mark.register_function)
            assert register_function.__name__ == mark.register_function
            logger.debug(
                f'registering marked function: '
                f'@{register_function!r}(*{mark.register_args}, **{mark.register_kwargs})({mark.marked_function})'
            )
            register_function(*mark.register_args, **mark.register_kwargs)(mark.marked_function)
        # end if

        self.states.register_state(name, state=new_state)
        instance_item = TeleMenuInstancesItem(
            machine=self, state=new_state, menu=menu_to_register
        )
        self.instances[name] = instance_item
        menu_to_register.register_state_instance(instance_item)
        return menu_to_register
    # end def

    def get_current_menu(self) -> Type[Union[None, 'Menu']]:
        """
        Get the current menu.
        Return `None` if is the `DEFAULT` state, or does not exist in the menu.

        :return: The current menu or None.
        """
        state = self.states.CURRENT
        if state == self.states.DEFAULT:
            logger.debug('State is default, so not a menu.')
            return None
        # end if
        if state.name not in self.instances:
            logger.debug('State has no menu registered here.')
            return None
        # end if
        return self.instances[state.name].menu
    # end def

    # noinspection PyMethodParameters
    def get_last_menu(self, activate=False) -> Union[None, Type['Menu']]:
        """
        Returns the previous menu in the history, or None if there is none.
        :return:
        """
        if not self.states.CURRENT.data.history:
            return None
        # end if
        current_menu_name = self.get_current_menu().id
        most_recent_menu_name = self.states.CURRENT.data.history[-1]
        assert most_recent_menu_name == current_menu_name  # fail = the current state was not added to the history
        last_menu_name = self.states.CURRENT.data.history[-2]
        if activate:
            self.states.CURRENT.data.history.pop(-1)
        # end if
        last_menu = self.instances[last_menu_name].menu
        if activate:
            last_menu.activate(add_history_entry=False)  # history already added, we're just jumping back
        # end if
        return last_menu
    # end def
# end class


class MenuData(object):
    message_id: Union[int, None]
    page: int
    data: JSONType

    def __init__(self, message_id: Union[int, None] = None, page: int = 0, data: JSONType = None):
        self.message_id = message_id
        self.page = page
        self.data = data
    # end def

    def to_dict(self) -> Dict[str, JSONType]:
        return {
            "message_id": self.message_id,
            "page": self.page,
            "data": self.data,
        }
    # end def

    @classmethod
    def from_dict(cls, data: Dict[str, JSONType]) -> 'Data':
        return cls(
            message_id=data['message_id'],
            page=data['page'],
            data=data['data'],
        )
    # end def

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'message_id={self.message_id!r}, '
            f'page={self.page!r}, '
            f'data={self.data!r}'
            ')'
        )
    # end def

    __str__ = __repr__
# end class


# TODO: there is needed a way to add your own stuff, e.g. you have other states than only menus...
class Data(object):
    menus: Dict[str, MenuData]  # keys are IDs.
    history: List[str]  # stack of IDs.

    def __init__(self, menus: Dict[str, JSONType] = None, history: List[str] = None):
        self.menus = {} if menus is None else menus
        self.history = [] if history is None else history
    # end def

    def to_dict(self) -> Dict[str, JSONType]:
        return {
            "menus": self.menus,
            "history": self.history,
        }
        # end def

    @classmethod
    def from_dict(cls, data: Dict[str, JSONType]) -> 'Data':
        return cls(
            menus={k: MenuData.from_dict(v) for k, v in data['menus'].items()},
            history=data['history'],
        )
    # end def

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'menus={self.menus!r}, '
            f'history={self.history!r}'
            ')'
        )
    # end def

    __str__ = __repr__
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

    tblueprint: ClassVar[TBlueprint]
    # noinspection PyMethodParameters
    @classproperty
    def tblueprint(cls: Type['Menu']) -> Union[TBlueprint, None]:
        if not cls._state_instance:
            return None
        # end if
        return cast(TeleMachine, cls._state_instance.machine).blueprint
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
    def send_message(cls, bot: Bot, chat_id: int) -> Message:
        """
        This function sends a message to a chat ID and stores the information about it in `menu.data.menus[menu.id].message_id`.

        :param chat_id:
        :return:
        """
        bot.send_message(
            chat_id=chat_id,
            text=cls.get_value(cls.text),
            parse_mode='html',
            disable_web_page_preview=True,
            disable_notification=False,
            # reply_to_message_id=None,
            reply_markup=cls.get_value(cls.reply_markup),
        )
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

    @classmethod
    def register_state_instance(cls, instance_item: TeleMenuInstancesItem):
        """
        Function to register a state.

        :param instance_item:
        :return:
        """
        super().register_state_instance(instance_item)

        # basically defining
        @instance_item.state.on_update('inline_query')
        def on_inline_query_wrapper(update: Update):
            result = cls.on_inline_query(update)
            cls.refresh()
        # end def
        cls.on_inline_query = instance_item.state.on_update(cls.on_inline_query, 'inline_query')
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

    @classmethod
    def refresh(cls, done: bool = False):
        """
        Edit the posted message to reflect new state, or post a new one if needed.
        # TODO: If a new message is to be posted, the new message_id must be tracked,
        # TODO: and maybe also the old keyboard removed.

        :param done: Set to true if this message is not the current any longer.
                     Used to e.g. include the selection in the message when the new menu is opened below.
        :return:
        """
        bot: Bot = cast(Bot, cls.bot)
        assert_type_or_raise(bot, Bot, parameter_name='bot')
        reply_markup = cls.get_keyboard() if not done else None
        bot.edit_message_text(
            text=cls.get_value(cls.text),
            chat_id=None,
            message_id=None,
            parse_mode='html',
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )
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
        """ returns the text for the button """
        pass
    # end def

    @abstractmethod
    def get_callback_data(self, data: Data) -> CallbackData:
        """ returns the button data to identify the button. """
        pass
    # end def
# end class


@dataclass(init=False, eq=False, repr=True)
class GotoMenu(ButtonMenu):
    MENU_TYPE = 'gotomenu'  # used for CallbackData.type

    menus: ClassValueOrCallableList['GotoButton']

    @classmethod
    @abstractmethod
    def menus(cls) -> List['GotoButton']:
        pass
    # end def


    @classmethod
    def get_buttons(cls) -> List[InlineKeyboardButton]:
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
    def send_message(cls, bot: Bot, chat_id: Union[int, str]):
        bot.send_message(
            chat_id=chat_id,
            text=cls.cls.get_value(cls.text),
            parse_mode='html',
            disable_web_page_preview=True,
            disable_notification=False,
            # reply_to_message_id=None,
            reply_markup=cls.get_keyboard(),
        )
    # end def
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
# end def


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
    def get_back_button(cls) -> Union[None, BackButton]:
        pass
    # end def

    @classmethod
    def reply_markup(cls) -> Union[None, ReplyMarkup]:
        return ForceReply(selective=True)
    # end def

    @classmethod
    def send_message(cls, bot: Bot, chat_id: int) -> Message:
        pass
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
        from pytgbot.api_types.receivable.media import File, PhotoSize
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
# end def


# ------------------------------
# TEST CLASSES
# here the stuff is implemented
# ------------------------------


telemenu = TeleMenuMachine()


@telemenu.register
class RegisterTestMenu(Menu):
    # noinspection PyNestedDecorators
    @classmethod
    @registerer.on_message
    def on_message_listener(cls, update: Update, msg: Message):
        """
        Handles callbackdata, registered by
        :param update:
        :return:
        """
        pass
    # end def

    @classmethod
    @registerer.on_command('init')
    def on_command_listener(cls, update: Update, text: Union[str, None]):
        """
        Handles callbackdata, registered by
        :param update:
        :return:
        :return:
        """
        pass
    # end def
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
