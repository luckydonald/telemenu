#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from luckydonaldUtils.logger import logging

__author__ = 'luckydonald'

import requests
from pytgbot.api_types.receivable.updates import Update, Message
from pytgbot.api_types.receivable.peer import Chat, User

from example_bot import app, API_KEY

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logging.add_colored_handler(level=logging.DEBUG)
# end if



update = Update(
    0,
    message=Message(
        date=1,
        message_id=3,
        chat=Chat(2, type='private'),
        from_peer=User(2, False, 'Test User'),
        text="/start"
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
        response = self.app.post(f'/income/{API_KEY}', json=update.to_array())
        self.assertEqual(response.status_code, 200)
    # end def
# end def
