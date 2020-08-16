
from tbot import BotHandler, Message
import re
import datetime
from psql_mock import Postgres
import bot_token


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
    match = re.search(r'(\/add).*"([\w\s]*)" (\d{1,2}.\d{1,2}.\d{1,4})',message.text)
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
    match = re.search(r'(\/del).*"([\w\s]*)"',message.text)
    if match:
        _, _name = match.groups()
        try:
            db.del_birthday(_name, message.chat_id)
        except KeyError:
            my_bot.send_message(message.chat_id, f'Нет дня рождения с таким именем')    
        my_bot.send_message(message.chat_id, f'Удален день рождение name={_name}')
    else:
        my_bot.send_message(message.chat_id, 'Wrong /del arguments. Use /del "[name]"')


@my_bot.recieve_command_decorator('/list')
def list_command(message : Message):
    '''
    Get /list command and send all birthdays specified for this chat to chat.
    '''
    b_list = db.get_all_birthdays(message.chat_id)
    formated_list = [f' {i} {b_list[i]}' for i in b_list]
    formated_list = '\n'.join(formated_list)
    my_bot.send_message(message.chat_id, f'Дни рождения:\n{formated_list}')


#TODO: add buttons view for select a name
@my_bot.recieve_command_decorator('/calc')
def calculate_command(message : Message):
    '''
    Calculate how much days left for birthday
    '''
    match = re.search(r'(\/calc).*"([\w\s]*)"',message.text)
    if match:
        _, _name = match.groups()
        try:
            b_dict = db.get_birthday(_name, message.chat_id)
        except KeyError:
            my_bot.send_message(message.chat_id, f'Нет дня рождения с таким именем')
            return
        #calculate time until birthday
        d,m,_ = map(int, b_dict['birth_date'].split('.'))
        now_date = datetime.date.today()
        b_date = datetime.date(day=d,month=m,year=now_date.year)
        if now_date > b_date:
            b_date = datetime.date(day=d,month=m,year=now_date.year+1)
        calc_date = b_date - now_date
    
        my_bot.send_message(message.chat_id, f'Осталось {calc_date.days} дней до дня рождения "{_name}"')
    else:
        my_bot.send_message(message.chat_id, 'Wrong /calc arguments. Use /calc "[name]" ')


def check_birthday():
    pass

def main():  
    while True:
        my_bot.polling()
    

if __name__ == '__main__':  
    try:
        main()
    except KeyboardInterrupt:
        exit()
