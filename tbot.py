'''
This module implement classes to simplify working with telegram bot api.

Classes:
    Message : telegram respons from server json wrapper
    BotHandler : bot to work with telegram api
'''

from typing import List, Set, Tuple, Dict, Generator
import requests  
import datetime
import re


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
        return self._message['text']

    @property
    def chat_id(self):
        return self._message['chat']['id']

    @property
    def chat_name(self):
        return self._message['chat']['first_name']

    @property
    def sender_first_name(self):
        return self._message['from']['first_name']
    
    @property
    def sender_last_name(self):
        return self._message['from']['last_name']
        


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
        self._handler_queue = []

    def get_updates(self, offset : int = None, timeout : int = 30) -> Dict:
        '''
        Get updates from telegram bot.
        '''
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id : str, text : str, markup = None) -> Dict:
        '''
        Send message to chat.
        '''
        params = {'chat_id': chat_id, 'text': text, 'reply_markup' : markup}
        method = 'sendMessage'
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

    def get_last_messages(self, timeout : int = 100) -> Generator:
        '''
        Get last updates from telegram for bot and transform them to Generator[Message]
        '''
        updates = self.get_last_updates(timeout=timeout)
        try:
            #подумать как ловить messege edited и callback
            print(updates)
            message_generator = (Message(i['message']) for i in updates)
        except KeyError:
            print(updates)
            message_generator = None
        return message_generator

    def polling(self) -> None:
        '''
        Bot polling routine.
        '''
        try: 
            messages = self.get_last_messages(500)           
        except ValueError:
            pass
        else:
            try:
                for i in messages:
                    for j in self._handler_queue:
                        j(i) 
            except KeyError:
                print('Was KeyError')

    def recieve_message_decorator(self, func):
        '''
        Decorator for functions that wait for recieve a message.
        '''
        def wrapper(*args, **kwargs):
                    func(*args, **kwargs)  
        self._handler_queue.append(wrapper)
        return wrapper
    
    def recieve_command_decorator(self, command : str):
        '''
        Decorator fabric for function that waiting to recieve command.
        '''
        def decorator(func):
            def wrapper(message : Message):
                if command in message.text:
                    func(message)
            self._handler_queue.append(wrapper)
            return wrapper
        return decorator

