'''
This module implement classes to simplify work with telegram bot api.

Classes:
    InlineButton : telegram inline button wraper
    Message : telegram message wrapper
    Callback : telegram callback wrapper
    BotHandler : bot to work with telegram api
'''

from typing import List, Set, Tuple, Dict, Generator
import requests  
import datetime
import re
import json


class InlineButton:
    '''
    Class wrapper that helps to create inline buttons for inline keyboards.
    '''
    def __init__(self, text, data, handler_name = None):
        self._button = {'text': text, 'callback_data': json.dumps({'handler' : handler_name ,'data' : data})}
    
    @property
    def button_dict(self):
        return self._button.copy()


class Message:
    '''
    Telegram message wrapper class.
    '''
    def __init__(self, message_json):
        self._message = message_json

    def __str__(self):
        return f'chat_id:{self.chat_id}, chat_name:{self.chat_name}\nfrom {self.sender_first_name} {self.sender_last_name}\ntext:{self.text}'

    @property
    def text(self):
        return self._message.get('text', '')

    @property
    def chat_id(self):
        return self._message['chat']['id']

    @property
    def message_id(self):
        return self._message['message_id']

    @property
    def chat_name(self):
        return self._message['chat']['first_name']

    @property
    def sender_first_name(self):
        return self._message['from']['first_name']
    
    @property
    def sender_last_name(self):
        return self._message['from']['last_name']
        

class Callback:
    '''
    Telegram callback wrapper uses to parse callback from inline keyboards etc.
    '''
    def __init__(self, callback_json):
        self._message = Message(callback_json['message'])
        self._callback_id = callback_json['id']
        self._data = json.loads(callback_json['data'])

    @property
    def message(self):
        return self._message

    @property
    def callback_id(self):
        return self._callback_id

    @property
    def id(self):
        return self._callback_id

    @property
    def data(self):
        data = self._data
        if type(data) == dict:
            return data.get('data', None)
        return data

    @property
    def handler(self):
        handler = None
        if type(self._data) == dict:
            handler = self._data.get('handler', None)
        return handler

    @property
    def chat_id(self):
        return self._message.chat_id


class BotHandler:
    '''
    Class that help works with telegram bot API.
    '''

    def __init__(self, token : str):
        '''
        Bot constructor.
        '''
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self._offset = None
        self._message_handler_queue = []
        self._callback_handler_queue = []

    def get_updates(self, offset : int = None, timeout : int = 30) -> Dict:
        '''
        Get updates from telegram bot.
        '''
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id : int, text : str, markup = None) -> Dict:
        '''
        Send message to chat.
        '''
        params = {'chat_id': chat_id, 'text': text, 'reply_markup' : markup}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, data=params)
        return resp

    def send_inline_keyboard(self, chat_id : int, text : str, buttons : List[List[InlineButton]]) -> Dict:
        '''
        Send inline keyboard to chat.
        '''
        buttons = [[j.button_dict for j in i] for i in buttons]
        markup = json.dumps({'inline_keyboard' : buttons })
        resp = self.send_message(chat_id, text, markup)
        return resp

    def edit_message(self, chat_id : int, message_id : int, text : str, markup = None) -> Dict:
        '''
        Edit message in chat.
        '''
        params = {'chat_id': chat_id, 'message_id' : message_id, 'text': text, 'reply_markup' : markup}
        method = 'editMessageText'
        resp = requests.post(self.api_url + method, data=params)
        return resp

    def get_last_updates(self, timeout : int = 30) -> Dict:
        '''
        Get last updates from telegram bot.
        '''
        result_json = self.get_updates(offset=self._offset, timeout=timeout)
        if len(result_json) > 0:
            last_update_id = result_json[-1]['update_id']
            self._offset = last_update_id + 1
        else:
            raise ValueError('Empty result!')
        #     self._offset = 0 #not sure about this
        return result_json

    def polling(self) -> None:
        '''
        Bot polling routine.
        '''
        try:
            updates = self.get_last_updates(200)
        except ValueError:
            return

        messages = filter(lambda x: x.get('message', False), updates)
        callbacks = filter(lambda x: x.get('callback_query', False), updates)

        for i in messages:
            msg = Message(i['message'])
            for j in self._message_handler_queue:
                j(msg)
        for i in callbacks:
            clbk = Callback(i['callback_query'])
            for j in self._callback_handler_queue:
                j(clbk)
        

    def recieve_message_decorator(self, func):
        '''
        Decorator for functions that wait for recieve a message.
        '''
        def wrapper(message : Message):
                    func(message)  
        self._message_handler_queue.append(wrapper)
        return wrapper
    

    def recieve_command_decorator(self, command : str):
        '''
        Decorator fabric for function that waiting to recieve command.
        '''
        def decorator(func):
            def wrapper(message : Message):
                if command in message.text:
                    func(message)
            self._message_handler_queue.append(wrapper)
            return wrapper
        return decorator


    def recieve_callback_decorator(self, callback_handler_name = None):
        '''
        Decorator for functions that wait for recieve a callback.
        '''
        def decorator(func):
            def wrapper(callback : Callback):
                if callback.handler == callback_handler_name:
                    func(callback)  
            self._callback_handler_queue.append(wrapper)
            return wrapper
        return decorator

