#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

logger = logging.getLogger(__name__)
logging.add_colored_handler(level=logging.DEBUG)
# end if
print('__name__', __name__)

from telemenu.machine import MarkForRegister



def decorator(func):
    func_to_mark = func
    if isinstance(func_to_mark, classmethod):
        # while an attribute of the the `@classmethod` wrapper can be set, every attribute read will be proxied to the function instead.
        # So it would be there, but we could never read it.
        # Instead we need to set the attribute on the function not on the classmethod wrapper.
        # https://t.me/c/1111136772/117738
        # https://stackoverflow.com/a/1677671/3423324#how-does-a-classmethod-object-work
        func_to_mark = func_to_mark.__get__(None, classmethod).__func__
    # end if
    setattr(func_to_mark, '_special_attr_', 'maybe ponies?')
    return func  # this is not func_to_mark, as we need to return the `@classmethod` one.
# end def


class Foo(object):
    @decorator
    @classmethod
    def method_one(cls, gnerf):
        return gnerf
    # end def

    @classmethod
    @decorator
    def method_two(cls, gnerf):
        return gnerf
    # end def

    @MarkForRegister.on_message
    @classmethod
    def method_mark_one(cls, gnerf):
        return gnerf
    # end def

    @classmethod
    @MarkForRegister.on_message
    def method_mark_two(cls, gnerf):
        return gnerf
    # end def


class DecoratorTests(unittest.TestCase):
    def test_one(self):
        method = Foo.method_one
        result = method('test')
        self.assertEqual(result, 'test')
        print(type(method))
        self.assertEqual(method._special_attr_, 'maybe ponies?')

    def test_two(self):
        method = Foo.method_two
        result = method('test')
        self.assertEqual(result, 'test')
        print(type(method))
        self.assertEqual(method._special_attr_, 'maybe ponies?')

    def test_mark_one(self):
        method = Foo.method_mark_one
        result = method('test')
        self.assertEqual(result, 'test')
        print(type(method))
        self.assertTrue(hasattr(method, MarkForRegister.StoredMark.MARK))

    def test_mark_two(self):
        method = Foo.method_mark_two
        result = method('test')
        self.assertEqual(result, 'test')
        print(type(method))
        self.assertTrue(hasattr(method, MarkForRegister.StoredMark.MARK))
