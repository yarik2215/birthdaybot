
from tbot import BotHandler, Message, Callback, InlineButton
import re
import datetime
from psql_mock import Postgres
import bot_token
import json

bot_token = bot_token.BOT_TOKEN
my_bot = BotHandler(bot_token)
db = Postgres()

@my_bot.recieve_command_decorator('/help')
def help_command(message : Message):
    '''
    Recieve /help command and send help information to chat.
    '''
    help_str = """ Этот бот поздравляет всех с Днем Рождения.\
    Для того чтобы он вас поздравил, ему нужно знать у кого когда день рождения,\
    для добавления дня рождения используйте команду /add "[имя]" [день].[месяц].[год] \
    Для удаление человека которого не нужно поздравлять используйте /del "[Имя]"

    Команды:
    /start
    /help
    /add "[имя]" [день].[месяц].[год]
    /del "[имя]"
    /list
    /calc "[имя]"
    """
    my_bot.send_message(message.chat_id, help_str)


@my_bot.recieve_command_decorator('/start')
def hello_message(message : Message) -> None:
    '''
    Handle /start and send hello msg to chat.
    '''
    my_bot.send_message(message.chat_id, f'Привет {message.sender_first_name}, я поздравительный бот. Если хочешь узнать больше напиши /help')


@my_bot.recieve_command_decorator('/add')
def add_command(message : Message):
    '''
    Recieve /add command and, add new birthday.
    '''
    match = re.search(r'(\/add)\S* (.*) (\d{1,2}.\d{1,2}.\d{1,4})',message.text)
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
        my_bot.send_message(message.chat_id, f'Добавлен день рождение name={_name} date={_date}')
    else:
        my_bot.send_message(message.chat_id, 'Wrong /add arguments. Use /add "[name]" [day].[month].[year]')
    # print(match)


@my_bot.recieve_command_decorator('/del')
def del_command(message : Message):
    '''
    Get /del command and delete birthday with specified name
    '''
    names = db.get_chat_birthdays(message.chat_id).keys()
    b_list = [[InlineButton('Cancel','Cancel','cancel')]]
    b_list.extend([[InlineButton(i,i,'del')] for i in names])
    my_bot.send_inline_keyboard(message.chat_id,'Кого удалить?',b_list)

@my_bot.recieve_callback_decorator('del')
def del_callback(callback : Callback):
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
    my_bot.edit_message(callback.chat_id, callback.message.message_id, 'Ну и ладно.')


@my_bot.recieve_command_decorator('/list')
def list_command(message : Message):
    '''
    Get /list command and send all birthdays specified for this chat to chat.
    '''
    b_list = db.get_chat_birthdays(message.chat_id)
    formated_list = [f' {i} {b_list[i].day}.{b_list[i].month}.{b_list[i].year}' for i in b_list]
    formated_list = '\n'.join(formated_list)
    my_bot.send_message(message.chat_id, f'Дни рождения:\n{formated_list}')

def calc_days(birth_date : datetime.date):
    d = birth_date.day
    m = birth_date.month
    now_date = datetime.date.today()
    b_date = datetime.date(day=d,month=m,year=now_date.year)
    if now_date > b_date:
        b_date = datetime.date(day=d,month=m,year=now_date.year+1)
    calc_date = b_date - now_date
    return calc_date.days

#TODO: add buttons view for select a name
@my_bot.recieve_command_decorator('/calc')
def calculate_command(message : Message):
    '''
    Calculate how much days left for birthday
    '''
    names = db.get_chat_birthdays(message.chat_id).keys()
    b_list = [[InlineButton('Cancel','Cancel','cancel')]]
    b_list.extend([[InlineButton(i,i,'calc')] for i in names])
    my_bot.send_inline_keyboard(message.chat_id,'Сколько дней осталось до дня рождения',b_list)
    
@my_bot.recieve_callback_decorator('calc')
def calc_callback(callback : Callback):    
    _name = callback.data
    try:
        b_dict = db.get_birthday(_name, callback.chat_id)
    except KeyError:
        my_bot.send_message(callback.chat_id, 'Упс ошибочка')
        return
    #calculate time until birthday
    # d,m,_ = map(int, b_dict['birth_date'].strftime('%d.%m.%Y').split('.'))
    days = calc_days(b_dict['birth_date'])
    my_bot.edit_message(callback.chat_id, callback.message.message_id, f'Осталось {days} дней до дня рождения "{_name}"')
    

@my_bot.recieve_command_decorator('/test')
def test_markup_command(message : Message):
    # m2 = ({
    # 'inline_keyboard': [
    #   [InlineButton('1', 'b1', 'test').button_dict],
    #   [{ 'text': 'Кнопка 2', 'callback_data': json.dumps({'handler' : 'test' ,'data' : '2'}) }],
    #   [{ 'text': 'Кнопка 3', 'callback_data': json.dumps({'handler' : 'test' ,'data' : '3'}) }]
    # ]
    # })
    # my_bot.send_message(message.chat_id, f'Тык', json.dumps(m2))
    buttons = [
        [InlineButton('1', 'b1', 'test')],
        [InlineButton('2', 'b2', 'test')],
        [InlineButton('3', 'b3', 'test')]
        ]
    my_bot.send_inline_keyboard(message.chat_id, 'Test', buttons)

@my_bot.recieve_callback_decorator('test')
def test_callback(callback : Callback):
    my_bot.edit_message(callback.chat_id, callback.message.message_id, f'U select {callback.data}')


#TODO: add class BirthdayHandler
class BirthdayHandler:
    
    def __init__(self):
        self._prev_date = None

    def check_birthday(self):
        cur_date = datetime.date.today()
        if self._prev_date != cur_date:
            self._prev_date = cur_date
            for chat_id, table in db.get_all_birthdays().items():
                for name, b_day in table.items():
                    try:
                        if b_day.day == cur_date.day and b_day.month == cur_date.month:
                            self.celebrate(name, b_day, chat_id)
                    except AttributeError:
                        return

    def celebrate(self, name, birth_date, chat_id):
        my_bot.send_message(chat_id, f'С днем рождения {name}!')


def main():  
    birthday_handler = BirthdayHandler()
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
