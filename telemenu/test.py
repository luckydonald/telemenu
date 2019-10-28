#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass, field as dataclass_field
from typing import Type, Dict, Union, List, ClassVar, Callable, Any, TypeVar, _tp_cache, Pattern

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


@dataclass
class Button(object):
    label: str
    id: Union[str, None]  # None means automatic
# end class


@dataclass
class GotoMenu(Menu):
    menus: ClassValueOrCallableList['GotoButton']
# end class


@dataclass
class GotoButton(Button):
    menu: ClassValueOrCallable[Menu]
# end class


class DoneButton(GotoButton):
    pass
# end class


@dataclass
class CheckboxMenu(Menu):
    checkboxes: ClassValueOrCallable['CheckboxButton']
# end class


@dataclass
class CheckboxButton(Button):
    selected: ClassValueOrCallable[bool] = False
# end class


@dataclass
class RadioMenu(Menu):
    radiobuttons: ClassValueOrCallable['RadioButton']    # TODO: check that max one has selected=True
# end class


class RadioButton(Button):
    pass
# end class


class TextMenuMetaclass(type):
    @staticmethod
    def _get_mixins_(bases):
        """Returns the type for creating enum members, and the first inherited
        enum class.

        bases: the tuple of bases that was given to __new__

        """
        if not bases:
            return object, TextMenu

        def _find_data_type(bases):
            if not issubclass(first_enum, TextMenu):
                raise TypeError("new enumerations should be created as "
                                "`TextMenu([mixin_type, ...] [data_type,] textmenu_type)`")

            for chain in bases:
                for base in chain.__mro__:
                    if base is object:
                        continue
                    elif '__new__' in base.__dict__:
                        if issubclass(base, TextMenu):
                            continue
                        return base

        # ensure final parent class is an Enum derivative, find any concrete
        # data type, and check that Enum has no members
        first_enum = bases[-1]
        member_type = _find_data_type(bases) or object
        return member_type, first_enum

    def __new__(metacls, cls, bases, classdict):
        # an Enum class is final once enumeration items have been defined; it
        # cannot be mixed with other types (int, float, etc.) if it has an
        # inherited __new__ unless a new __new__ is defined (or the resulting
        # class will fail).
        parser_type, first_enum = metacls._get_mixins_(bases)
        textmenu_class = super().__new__(metacls, cls, bases, classdict)
        textmenu_class._parser_type_ = parser_type
    # end def
# end class

metadic={}


def _generatemetaclass(bases,metas,priority):
    trivial=lambda m: sum([issubclass(M,m) for M in metas],m is type)
    # hackish!! m is trivial if it is 'type' or, in the case explicit
    # metaclasses are given, if it is a superclass of at least one of them
    metabs=tuple([mb for mb in map(type,bases) if not trivial(mb)])
    metabases=(metabs+metas, metas+metabs)[priority]
    if metabases in metadic: # already generated metaclass
        return metadic[metabases]
    elif not metabases: # trivial metabase
        meta=type
    elif len(metabases)==1: # single metabase
        meta=metabases[0]
    else: # multiple metabases
        metaname="_"+''.join([m.__name__ for m in metabases])
        meta=makecls()(metaname,metabases,{})
    return metadic.setdefault(metabases,meta)

def makecls(*metas,**options):
    """Class factory avoiding metatype conflicts. The invocation syntax is
    makecls(M1,M2,..,priority=1)(name,bases,dic). If the base classes have
    metaclasses conflicting within themselves or with the given metaclasses,
    it automatically generates a compatible metaclass and instantiate it.
    If priority is True, the given metaclasses have priority over the
    bases' metaclasses"""

    priority=options.get('priority',False) # default, no priority
    return lambda n,b,d: _generatemetaclass(b,metas,priority)(n,b,d)


class TextMenu(metaclass=TextMenuMetaclass):
    def _parse(self, text: str) -> Any:
        raise NotImplementedError('Subclasses must implement that.')
    # end def
# end class


class TextStrMenu(str, TextMenu):
    def _parse(self, text: str) -> str:
        return text
    # end def
# end class


class TextIntMenu(int, TextMenu):
    def _parse(self, text: str) -> int:
        return int(text)
    # end def
# end class


class TextFloatMenu(float, TextMenu):
    def _parse(self, text: str) -> float:
        return float(text)
    # end def
# end class


class TextPasswordMenu(str, TextMenu):
    def _parse(self, text: str) -> str:
        return text
    # end def
# end class


class TextEmailMenu(TextMenu[str]):
    def _parse(self, text: str) -> str:
        if "@" not in text or "." not in text:  # TODO: improve validation.
            raise ValueError('No good email.')
        return text
    # end def
# end class


class TextTelMenu(str, TextMenu):
    def _parse(self, text: str) -> str:
        # TODO: add validation.
        return text
    # end def
# end class


@dataclass
class TextUrlMenu(str, TextMenu):
    allowed_protocols: List[str] = dataclass_field(default_factory=lambda: ['http', 'https'])

    def _parse(self, text: str) -> str:
        if not any(text.startswith(protocol) for protocol in self.allowed_protocols):
            raise ValueError('Protocol not allowed')
        # end if
        # TODO: improve validation.
        return text
    # end def
# end class


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

