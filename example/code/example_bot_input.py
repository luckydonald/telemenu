#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from typing import cast

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

import requests
from pytgbot.api_types.receivable.updates import Update, Message, CallbackQuery
from pytgbot.api_types.receivable.peer import Chat, User

from example_bot import app, API_KEY, bot, menus, MainMenu
from unittest import mock  # https://stackoverflow.com/a/15775162/3423324
mock.patch('requests.get', mock.Mock(side_effect = lambda k:{'aurl': 'a response', 'burl' : 'b response'}.get(k, 'unhandled request %s'%k)))
mock.patch('requests.post', mock.Mock(side_effect = lambda k:{'aurl': 'a response', 'burl' : 'b response'}.get(k, 'unhandled request %s'%k)))



logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if


user = User(2, False, 'Test User')

message = Message(
    date=1,
    message_id=3,
    chat=Chat(user.id, type='private'),
    from_peer=user,
    text="/start"
)

start_update = Update(
    0,
    message=message,
)

callback_update = Update(
    4,
    callback_query=CallbackQuery(
        id='5',
        from_peer=user,
        chat_instance='what is this?',
        data='{"type": "gotomenu", "id": null, "value": "TEST_MENU"}',
        message=message,
    )
)


class BasicTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        self.app = app.test_client()
        self.assertEqual(app.debug, False)
    # end def

    # executed after each test
    def tearDown(self):
        pass
    # end def

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    # end def

    def test_update_start(self):
        response = self.app.post(f'/income/{API_KEY}', json=start_update.to_array())
        self.assertEqual(response.status_code, 200)
    # end def

    def test_callback_query(self):
        # inject the state after the /start command
        from telemenu.machine import TeleStateMachineMenuSerialisationAdapter
        cast(TeleStateMachineMenuSerialisationAdapter, menus.states).CURRENT.set_update(start_update)
        MainMenu.activate()

        # send the button press's callback update
        response = self.app.post(f'/income/{API_KEY}', json=callback_update.to_array())
        self.assertEqual(response.status_code, 200)
    # end def

    def test_callback_query2(self):
        # inject the state after the /start command
        response = self.app.post(f'/income/{API_KEY}', json=start_update.to_array())
        self.assertEqual(response.status_code, 200)

        # send the button press's callback update
        response = self.app.post(f'/income/{API_KEY}', json=callback_update.to_array())
        self.assertEqual(response.status_code, 200)
    # end def
# end def
