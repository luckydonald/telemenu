#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import inspect
from luckydonaldUtils.exceptions import assert_type_or_raise
from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType
from teleflask.server.blueprints import TBlueprintSetupState
from dataclasses import dataclass
from teleflask import TBlueprint, Teleflask
from telestate import TeleState, TeleStateMachine
from typing import Callable, Tuple, Dict, Any, Union, Type, Generator, List, TYPE_CHECKING

from .data import Data
if TYPE_CHECKING:
    from .data import MenuData
    from .menus import Menu
# end if

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class TeleStateMachineMenuSerialisationAdapter(TeleStateMachine):
    """
    Normal TeleStateMachine, but with custom (de)serialisation methods,
    directly converting it to and from the `Data` type.
    """
    @classmethod
    def deserialize(cls, state_name, db_data):
        logger.debug(f'serializing db data {db_data}')
        array: Union[Dict[str, JSONType], None] = super(cls, cls).deserialize(state_name, db_data)
        logger.debug(f'deserializing array {db_data}')
        if array is None:
            # no data yet, so we provide a empty skeleton of data
            return Data(menus={}, history=[])
        # end if
        return Data.from_dict(array)
    # end def

    @classmethod
    def serialize(cls, state_name, state_data: Union['Data', None]):
        data = None if state_data is None else state_data.to_dict()
        return super(cls, cls).serialize(state_name, data)

    def process_result(self, update, result):
        """
        Send the result.
        It may be a :class:`Message` or a list of :class:`Message`s
        Strings will be send as :class:`TextMessage`, encoded as raw text.

        :param update: A telegram incoming update
        :type  update: TGUpdate | type(Menu)

        :param result: Something to send.
        :type  result: Union[List[Union[Message, str]], Message, str]

        :return: List of telegram responses.
        :rtype: list
        """
        from telemenu.menus import Menu
        logger.debug(f'Processing result: {result!r}')
        if result and issubclass(result, Menu):
            return result.send()
        # end if
        return super().process_result(update, result)
    # end def
# end class


@dataclass(init=False, repr=True)
class TeleMenuInstancesItem(object):
    """
    This holds a menu and a telestate to register functions to.
    """
    machine: 'TeleMenuMachine'
    state: TeleState
    menu: Type['telemenu.menus.Menu']

    def __init__(self, machine: 'TeleMenuMachine', state: TeleState, menu: Type['telemenu.menus.Menu']):
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


class MarkForRegister(object):
    """
    Mark functions to be included in the menu's state's tblueprint,
    as soon as that is assigned.

    Basically first the decorators next to the functions in the class are executed,
    and a marker is set.
    `function._tmenu_mark_ = MarkForRegister.StoreMark(...)`

    Later this can be retrieved with `MarkForRegister.collect_marked_functions(cls)`.
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
        logger.debug(f'marking function {menu_function!r} as {register_function!r}')
        setattr(
            menu_function,
            MarkForRegister.StoredMark.MARK,
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
        :param menu: The menu we want to collect the @MarkForRegister.* stuff on.
        :return:
        """
        functions = inspect.getmembers(menu, inspect.isroutine)
        logger.debug(f'collecting functions of class {menu!r}, checking {[name for name, _ in functions]!r}.')
        for name, method in functions:
            if not hasattr(method, MarkForRegister.StoredMark.MARK):  # this might wake it up.
                method = getattr(menu, name)
            # end if
            if hasattr(method, MarkForRegister.StoredMark.MARK):
                logger.debug(f'found marked function {name!r}.')
                mark: cls.StoredMark = getattr(method, MarkForRegister.StoredMark.MARK)
                mark.register_name = name
                yield mark
            # end if
        # end for
    # end def

    @classmethod
    def collect_marked_functions(cls, menu: Type['Menu']) -> List['StoredMark']:
        """
        Method generating returning a list of all previously marked functions.
        :param menu: The menu we want to collect the @MarkForRegister.* stuff on.
        :return:
        """
        return list(cls.collect_marked_functions_iter(menu))
    # end def

    @staticmethod
    def _build_listener(register_function):
        logger.debug(f'building listener decorator for function {register_function!r}')
        def decorator_function(*required_keywords: Tuple[str]) -> Union[Callable,  Callable[[Callable], Callable]]:
            """
            Like `BotCommandsMixin.on_message`, but for a static `Menu`.
            """
            logger.debug('waiting for a function to mark...')
            def actual_wrapping_method(function:  Callable):
                logger.debug(f'marking function {function!r}')
                MarkForRegister._mark_function(function, register_function, *required_keywords)
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
    # end def
# end class


# noinspection PyTypeHints
MarkForRegister.on_message: Callable[[], Callable] = staticmethod(getattr(MarkForRegister, '_build_listener')('on_message'))
# noinspection PyTypeHints
MarkForRegister.on_command: Callable = staticmethod(getattr(MarkForRegister, '_build_listener')('on_command'))
# noinspection PyTypeHints
MarkForRegister.on_update: Callable = staticmethod(getattr(MarkForRegister, '_build_listener')('on_update'))


@dataclass(init=False, repr=True)
class TeleMenuMachine(object):
    instances: Dict[str, TeleMenuInstancesItem]
    states: Union[TeleStateMachineMenuSerialisationAdapter, TeleStateMachine]

    def __init__(self, states: TeleStateMachineMenuSerialisationAdapter = None, database_driver=None, teleflask_or_tblueprint=None):
        assert_type_or_raise(states, TeleStateMachineMenuSerialisationAdapter, None, parameter_name='states')
        self.instances = {}
        self.states = states
        if not self.states:
            self.states = TeleStateMachineMenuSerialisationAdapter(__name__, database_driver, teleflask_or_tblueprint)
        # end def
    # end def

    mark_for_register = MarkForRegister

    def register(self, menu_to_register: Type['Menu']) -> Type['Menu']:
        """
        Creates a TeleState for the class and registers the overall menu loading structure..
        Note that the `id` attribute can be used to overwrite the custom name with a different function.
        :param menu_to_register: The menu to register
        :return: the class again, unchanged.
        """
        from .menus import Menu
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
        mark: MarkForRegister.StoredMark
        for mark in MarkForRegister.collect_marked_functions_iter(menu_to_register):
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

    def register_bot(self, teleflask_or_tblueprint: Union[TBlueprintSetupState, TBlueprint, Teleflask]):
        """
        Registers an bot to use with the internal blueprint of the TeleStateMachine.

        :param tblueprint: The Teleflask instance or blueprint to use.
        :type  teleflask_or_tblueprint: Teleflask | TBlueprint
        :return:
        """
        return self.states.register_bot(teleflask_or_tblueprint)
    # end def

    def get_current_menu(self) -> Union[None, Type['Menu']]:
        """
        Get the current menu.
        Return `None` if is the `DEFAULT` state, or does not exist in the menu.

        :return: The current menu or None.
        :rtype: Menu|None
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
