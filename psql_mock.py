from typing import List, Dict
import datetime
import pickle

class Postgres:
    '''
    Postgres mock using pickle and built-in buffer for birthdays.
    '''
    
    def __init__(self):
        try:
            with open('bdata.data','xb') as f:
                pickle.dump(dict(),f)
                self._table = dict()
        except FileExistsError:
            with open('bdata.data','rb') as f:
                self._table = pickle.load(f)

    def _update_datafile(self):
        with open('bdata.data','wb') as f:
            pickle.dump(self._table,f)

    def have_name(self, name : str, chat_id : str) -> bool:
        chat_table = self._table.get(chat_id, dict())
        res = name in chat_table
        return res

    def add_birthday(self, name : str, birth_date : str, chat_id : str):
        name = name.strip()
        if self.have_name(name, chat_id):
            raise KeyError('Already have birthday with this name!')
        d, m, y = map(int,birth_date.split('.'))
        if chat_id not in self._table:
            self._table[chat_id] = dict()
        self._table[chat_id][name] = datetime.date(year=y,month=m,day=d).strftime('%d.%m.%Y')
        self._update_datafile()

    def del_birthday(self, name : str, chat_id : str):
        name = name.strip()
        if not self.have_name(name, chat_id):
            raise KeyError('There is not birthday with this name!')
        self._table[chat_id].pop(name)
        self._update_datafile()

    def get_all_birthdays(self, chat_id : str) -> Dict:
        return self._table.get(chat_id, dict())

    def get_birthday(self, name : str, chat_id : str) -> Dict:
        name = name.strip()
        if not self.have_name(name, chat_id):
            raise KeyError('There is not birthday with this name!')
        return {'name' : name, 'birth_date' : self._table[chat_id][name], 'chat_id' : chat_id}

if __name__ == '__main__':
    db = Postgres()
    print(db.get_all_birthdays('123'))
    db.add_birthday('name','1.2.3','123')
