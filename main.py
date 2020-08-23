
from tbot import BotHandler, Message, Callback, InlineButton
import re
import datetime
from database import Database
import bot_token
import json

token = bot_token.BIRTHDAY_BOT_TOKEN
my_bot = BotHandler(token)
db = Database('data.db')


class BirthdayHandler:
    '''
    BirthdayHandler class implement functions to find today's birthdays and celebrate.
    '''

    def __init__(self):
        '''
        BirthdayHandler constructor
        '''
        self._prev_date = None

    def check_birthday(self):
        '''
        Check there are birthdays today.
        '''
        cur_date = datetime.date.today()
        if self._prev_date != cur_date:
            self._prev_date = cur_date
            b_list = db.get_birthdays_by_date(cur_date.strftime('%d.%m.%Y'))
            for i in b_list:
                self.celebrate(name=i['name'],birth_date=i['birth_date'],chat_id=i['chat_id'])
            

    def celebrate(self, name, birth_date, chat_id):
        '''
        Celebrates the birthday.
        '''
        my_bot.send_message(chat_id, f'С днем рождения {name}! 🎂😘')


    def check_new_birthday(self, name, birth_date, chat_id):
        '''
        Check if selected birthday is tooday.
        '''
        c_date = datetime.date.today()
        d,m,_ = map(int, birth_date.split('.'))
        if d == c_date.day and m == c_date.month:
            self.celebrate(name, birth_date, chat_id)
        

birthday_handler = BirthdayHandler()



@my_bot.recieve_command_decorator('/help')
def help_command(message : Message):
    '''
    Recieve /help command and send help information to chat.
    '''
    help_str = """ Этот бот поздравляет всех с Днем Рождения.\
    Для того чтобы он вас поздравил, ему нужно знать у кого когда день рождения,\
    для добавления дня рождения используйте команду /add [имя] [день].[месяц].[год] , например "/add test 1.1.1111"\
    Для удаление человека которого не нужно поздравлять используйте /del

    Команды:
    /start
    Пока сообщение приветствия.
    /help
    Показывает данное сообщение с описанием бота.
    /add [имя] [день].[месяц].[год]
    Добавляет новый День Рождения Пример "/add test 1.1.1111"
    /del 
    Показывает список для выбора какой День Рождение нужно удалить.
    /list
    Показывает все Дни Рождения.
    /calc 
    Подсчитывает сколько осталось дней до выбранного Дня Рождения.

    Исходники 😍 лежат тут: https://github.com/yarik2215/birthdaybot/tree/dev_callback
    """
    my_bot.send_message(message.chat_id, help_str)


@my_bot.recieve_command_decorator('/start')
def hello_message(message : Message) -> None:
    '''
    Handle /start and send hello msg to chat.
    '''
    my_bot.send_message(message.chat_id, f'Привет {message.sender_first_name}, я поздравительный бот. Если хочешь узнать больше напиши /help 😊')


@my_bot.recieve_command_decorator('/add')
def add_command(message : Message):
    '''
    Recieve /add command and, add new birthday.
    '''
    match = re.search(r'(\/add)\S* (.*) (\d{1,2}\.\d{1,2}\.\d{1,4})',message.text)
    if match:
        _, _name, _date = match.groups()
        try:
            db.add_birthday(_name, _date, message.chat_id)
        except ValueError:
            my_bot.send_message(message.chat_id, 'Упс, неправильная дата.')
            return    
        except KeyError:
            my_bot.send_message(message.chat_id, 'Упс, такое имя уже есть.')    
            return
        my_bot.send_message(message.chat_id, f'Добавлен день рождение😃\n{_name} {_date}')
        #check if added birthday is today
        birthday_handler.check_new_birthday(_name, _date, message.chat_id)
    else:
        my_bot.send_message(message.chat_id, 'Wrong /add arguments. Use /add "[name]" [day].[month].[year]')
    # print(match)


@my_bot.recieve_command_decorator('/del')
def del_command(message : Message):
    '''
    Get /del command and delete birthday with specified name
    '''
    names = db.get_chat_birthdays(message.chat_id)
    b_list = [[InlineButton('Cancel','Cancel','cancel')]]
    b_list.extend([[InlineButton(text = i['name'], data = i['name'], handler_name = 'del')] for i in names])
    my_bot.send_inline_keyboard(message.chat_id,'Кого удалить?',b_list)

@my_bot.recieve_callback_decorator('del')
def del_callback(callback : Callback):
    '''
    Del command callback. Del selected birthday.
    '''
    text = None
    try:
        name = callback.data
        db.del_birthday(name, callback.chat_id)
        text = f'{name} удален.'
    except KeyError:
        text = 'Упс, какая-то ошибочка)'
    my_bot.edit_message(callback.chat_id, callback.message.message_id, text)


@my_bot.recieve_callback_decorator('cancel')
def del_cancel_callback(callback : Callback):
    '''
    Cancel inline button selected callback handler.
    '''
    my_bot.edit_message(callback.chat_id, callback.message.message_id, 'Ну и ладно.😒')


@my_bot.recieve_command_decorator('/list')
def list_command(message : Message):
    '''
    Get /list command and send all birthdays specified for this chat to chat.
    '''
    b_list = db.get_chat_birthdays(message.chat_id)
    formated_list = [f' {i["name"]} {i["birth_date"]}' for i in b_list]
    formated_list = '\n'.join(formated_list)
    my_bot.send_message(message.chat_id, f'Дни рождения🎂:\n{formated_list}')


def calc_days(birth_date : datetime.date):
    '''
    Calculates how many days left until this date not included year
    '''
    d = birth_date.day
    m = birth_date.month
    now_date = datetime.date.today()
    b_date = datetime.date(day=d,month=m,year=now_date.year)
    if now_date > b_date:
        b_date = datetime.date(day=d,month=m,year=now_date.year+1)
    calc_date = b_date - now_date
    return calc_date.days

@my_bot.recieve_command_decorator('/calc')
def calculate_command(message : Message):
    '''
    Calculate how much days left for birthday
    '''
    names = db.get_chat_birthdays(message.chat_id)
    b_list = [[InlineButton('Cancel','Cancel','cancel')]]
    b_list.extend([[InlineButton(text = i['name'], data = i['name'], handler_name = 'calc')] for i in names])
    my_bot.send_inline_keyboard(message.chat_id, 'Сколько дней осталось до дня рождения', b_list)
    
@my_bot.recieve_callback_decorator('calc')
def calc_callback(callback : Callback):    
    '''
    Calculate callback, send how much days left until selected birthday.
    '''
    _name = callback.data
    try:
        b_dict = db.get_birthday(_name, callback.chat_id)
    except KeyError:
        my_bot.send_message(callback.chat_id, 'Упс ошибочка')
        return
    d,m,y = map(int, b_dict['birth_date'].split('.'))
    days = calc_days(datetime.date(y,m,d))
    my_bot.edit_message(callback.chat_id, callback.message.message_id, f'Осталось {days} дней до дня рождения "{_name}"')
    

@my_bot.recieve_command_decorator('/test')
def test_markup_command(message : Message):
    '''
    Recieve /test command for tetsing inline keyboard.
    '''
    buttons = [
        [InlineButton('1', 'b1', 'test')],
        [InlineButton('2', 'b2', 'test')],
        [InlineButton('3', 'b3', 'test')]
        ]
    my_bot.send_inline_keyboard(message.chat_id, 'Test', buttons)


@my_bot.recieve_callback_decorator('test')
def test_callback(callback : Callback):
    '''
    /test Inline keyboard callback, edit message with inline keyboard depends on your answer
    '''
    my_bot.edit_message(callback.chat_id, callback.message.message_id, f'U select {callback.data}')



def main():  
    print('Bot started!')
    try:
        while True:
            birthday_handler.check_birthday()
            my_bot.polling()
    finally:
        #add my_bot.stop()
        pass    


if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        print('Bot stoped!')
        exit()
