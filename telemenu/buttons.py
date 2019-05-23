# -*- coding: utf-8 -*-
from typing import Any, Union

from luckydonaldUtils.logger import logging
from luckydonaldUtils.typing import JSONType

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


class MenuButton(object):
    label: str
    goto: Union[str, 'Menu']
    action: Any

    def __init__(self, label: str, goto: Union[str, 'Menu'], variable: str = None, value: JSONType = None):
        """
        A Button navigation to a different menu, optionally setting a value.

        :param label:  The displayed text of the button
        :param goto:   Which Menu to go next.
        :param variable:  If it should store something in the state data, this is the variable name
        :param value:     If it should store something in the state data, this is the variable value
        """
        self.label = label
        self.goto = goto
        self.variable = variable
        self.value = value
    # end def
# end class


class ToggleButton(object):
    def __init__(self, label_on: str, label_off: str, variable: str, default: bool):
        """
        A Button working like a checkbox, switching between on and off. Stores state in a a value

        :param label_on:  The displayed text of the button if turned on.
        :param label_off: The displayed text of the button if turned off.
        :param variable:  Where in the state it should store the toggle value.
        :param default:   If it should start with True or False.
        """
        self.label_on = label_on
        self.label_off = label_off
        self.variable = variable
        self.default = default
    # end def
# end class
