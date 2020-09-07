'''
This module implements API for working with birthday database, its SQLite database.

Classes:
    Database
'''

from typing import List, Dict, Tuple
import datetime
import re
import sqlite3

BIRTHDAY_FIELDS = ('name','birth_date','chat_id')

class Database:
    '''
    Class that implements layer between birthday_bot and sqlite database.
    '''
    
    def __init__(self, db_name : str):
        '''
        Database constructor.
        '''
        self.db_name = db_name
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''CREATE TABLE "birthdays" (
            "hash"	text NOT NULL UNIQUE,
            "name"	text NOT NULL,
            "date"	text NOT NULL,
            "chat_id"	long NOT NULL
            );''')
            conn.commit()
        except sqlite3.OperationalError:
            print('Table already exists')
        finally:
            conn.close()


    @staticmethod
    def validate_date(birth_date : str) -> str:
        '''
        Validate date. And return at as string with format day.month.year .
        '''
        d, m, y = map(int, birth_date.split('.'))
        res = datetime.date(day=d, month=m, year=y)
        return res.strftime('%d.%m.%Y')

    @staticmethod
    def validate_name(name : str) -> str:
        '''
        Validate name and return formated string.
        '''
        return name.strip()


    def add_birthday(self, name : str, birth_date : str, chat_id : str):
        '''
        Add birthday to database.
        '''
        name = self.validate_name(name)
        values = (f'{name}:{chat_id}', name, self.validate_date(birth_date), chat_id)
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('INSERT INTO birthdays VALUES (?,?,?,?)', values)
            conn.commit()
        except sqlite3.IntegrityError:
            raise KeyError(f'Name {name} already exists!')
        finally:
            conn.close()        

    def del_birthday(self, name : str, chat_id : int):
        '''
        Delete birthday with specified name and chat_id from database. 
        '''
        name = self.validate_name(name)
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('DELETE FROM birthdays WHERE name=? AND chat_id=?', (name, chat_id) )
            conn.commit()
        except sqlite3.IntegrityError:
            raise KeyError(f'No name {name} in chat {chat_id}!')
        finally:
            conn.close()

    def get_chat_birthdays(self, chat_id : int) -> Tuple:
        '''
        Get all birthdays from selected chat.
        '''
        b_list = tuple()
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            b_list = c.execute('SELECT name, date, chat_id FROM birthdays WHERE chat_id=?', (chat_id,))
            b_list = [dict(zip(BIRTHDAY_FIELDS, i)) for i in b_list]
        except sqlite3.IntegrityError:
            raise KeyError('No instances with this chat_id.')
        finally:
            conn.close()
        
        return tuple(b_list)


    def get_all_birthdays(self) -> Tuple:
        '''
        Get all birthdays from database.
        '''
        b_list = tuple()
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            b_list = tuple(c.execute('SELECT name, date, chat_id FROM birthdays'))
            b_list = [dict(zip(BIRTHDAY_FIELDS, i)) for i in b_list]
        finally:
            conn.close()
        return tuple(b_list)


    def get_birthdays_by_date(self, birth_date : str) -> Tuple:
        '''
        Select birthday with selected day and month from database.
        '''
        birth_date = self.validate_date(birth_date)
        b_list = tuple()
        d,m,_ = birth_date.split('.')
        pattern = f'{d}\\.{m}\\.'
        # print(f'SELECT * FROM birthdays WHERE date REGEXP "{pattern}"')

        try:
            conn = sqlite3.connect(self.db_name)
            conn.create_function('regexp', 2, lambda x, y: 1 if re.search(x,y) else 0)
            c = conn.cursor()
            c.execute(f'SELECT name, date, chat_id FROM birthdays WHERE date REGEXP ?', (pattern,))
            b_list = c.fetchall()
            b_list = [dict(zip(BIRTHDAY_FIELDS, i)) for i in b_list]
        finally:
            conn.close()
        return tuple(b_list)


    def get_birthday(self, name : str, chat_id : int) -> Tuple:
        '''
        Get birthday with selected name and selected chat_id
        '''
        name = self.validate_name(name)
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('SELECT name, date, chat_id FROM birthdays WHERE name=? AND chat_id=?', (name, chat_id) )
            b_day = c.fetchone()
            if b_day:
                b_day = dict(zip(BIRTHDAY_FIELDS, b_day))
            else: 
                b_day = dict()
        finally:
            conn.close()
        return b_day




if __name__ == '__main__':
    db = Database('test.db')

    try:
        db.del_birthday('noname',0)
    except KeyError:
        print('no name with chat_id')

    try:
        db.add_birthday('test1','1.1.1996',1)
        db.add_birthday('test2','1.1.1996',1)
        db.add_birthday('test3','2.1.1996',1)
        db.add_birthday('test4','1.1.2001',1)
        db.add_birthday('wrong_date','231.21.1996',1)
    except KeyError:
        print('name already exist')
    except ValueError:
        print('WrongDate')
    
    print('All'.center(50,'_'))
    print(db.get_all_birthdays())
    print('By date'.center(50,'_'))
    print(db.get_birthdays_by_date('1.1.1996'))
    print(db.get_birthdays_by_date('2.1.1998'))

    try:
        db.del_birthday('test1',1)
        db.del_birthday('wrong_name',1)
    except KeyError:
        print ('no this name in table')

    print('All'.center(50,'_'))
    print(db.get_all_birthdays())
    print('By name'.center(50,'_'))
    print(db.get_birthday('test2',1))
    print(db.get_birthday('noname',1))
