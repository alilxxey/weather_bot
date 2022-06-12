import telebot
import requests
from datetime import time, date, datetime, timedelta, timezone
import schedule
import time
from multiprocessing.context import Process


TOKEN = '5118258895:AAGJd5IPGrPrAnFM7DTVWSyn2RYdtVwSkcA'  # токен бота

weather_code = {'4': 'Дым',  # соответствие кода погоды и его строкового представления (для обработки зответа на запрос gismeteo)
                '5': 'Мгла',
                '6': 'Пыльная',
                '7': 'Пыльная',
                '8': 'Пыльные',
                '9': 'Пыльная',
                '10': 'Дымка',
                '11': 'Туман',
                '12': 'Туман',
                '13': 'Зарница',
                '18': 'Шквалы',
                '19': 'Смерч',
                '20': 'Морось',
                '24': 'Гололед',
                '25': 'Ливень',
                '27': 'Град',
                '28': 'Туман',
                '30': 'Пыльная',
                '31': 'Пыльная',
                '32': 'Пыльная',
                '33': 'Пыльная',
                '34': 'Пыльная',
                '35': 'Пыльная',
                '36': 'Поземок',
                '37': 'Сильный',
                '38': 'Метель',
                '39': 'Сильная',
                '40': 'Туман',
                '41': 'Туман',
                '42': 'Туман',
                '43': 'Туман',
                '44': 'Туман',
                '45': 'Туман',
                '46': 'Туман',
                '47': 'Туман',
                '48': 'Туман',
                '49': 'Туман',
                '50': 'Небольшая',
                '51': 'Морось',
                '52': 'Морось',
                '53': 'Морось',
                '54': 'Сильная',
                '55': 'Морось',
                '56': 'Небольшая',
                '57': 'Морось',
                '66': 'Гололед',
                '67': 'Гололед',
                '68': 'Дождь',
                '69': 'Дождь',
                '74': 'Снегопад',
                '75': 'Снегопад',
                '76': 'Ледяные',
                '77': 'Снежные',
                '78': 'Снежные',
                '79': 'Ледяной',
                '81': 'Ливень',
                '82': 'Сильный',
                '83': 'Небольшие',
                '84': 'Ливень',
                '87': 'Снежная',
                '88': 'Снежная',
                '89': 'Слабый',
                '90': 'Град',
                '93': 'Град',
                '94': 'Град',
                '96': 'Град',
                '99': 'Град',
                '104': 'Мгла',
                '105': 'Мгла',
                '110': 'Дымка',
                '111': 'Ледяные',
                '112': 'Зарница',
                '118': 'Шквалы',
                '120': 'Туман',
                '122': 'Морось',
                '125': 'Гололёд',
                '130': 'Туман',
                '131': 'Туман',
                '132': 'Туман',
                '133': 'Туман',
                '134': 'Туман',
                '135': 'Туман',
                '147': 'Осадки',
                '148': 'Сильные',
                '150': 'Морось',
                '151': 'Небольшая',
                '152': 'Морось',
                '153': 'Сильная',
                '154': 'Небольшая',
                '155': 'Морось',
                '156': 'Сильная',
                '164': 'Гололед',
                '165': 'Гололед',
                '166': 'Гололед',
                '174': 'Слабая',
                '175': 'Ледяная',
                '176': 'Сильная',
                '177': 'Снежные',
                '178': 'Ледяные',
                '180': 'Ливневый',
                '189': 'Град',
                '193': 'Град',
                '196': 'Град',
                '199': 'Смерч',
                '280': 'Ливневый',
                '380': 'Ливневые',
                '500': 'Осадки',
                '501': 'Сильные',
                '528': 'Морозный',
                '568': 'Небольшие'}

bot = telebot.TeleBot(TOKEN)  # инициализация бота


class DataBase:  # класс, в котором хранится информация о пользователях
    def __init__(self):  # инициализация, создание словаря
        self.content = {}

    def new_obj(self, id, latitude=None, longitude=None, name=None, notifications=True):  # создание новоог объекта, записывается в self.content
        self.content[str(id)] = {'name': name,
                                 'latitude': latitude,
                                 'longitude': longitude,
                                 'notifications': notifications,
                                 'utc': 3}

    def __getitem__(self, item):  # вызывается при обращении к объекту по ключу, возвращает информацию о пользователе
        try:
            print(self.content)
            return self.content[str(item)]
        except Exception as e:
            raise KeyError(f'wrong id/no id in DB, {e}')

    def includes(self, id):  # проверяет, есть ли данный пользователь в БД
        return str(id) in self.content.keys()

    def change_loc(self, id, latitude=0, longitude=0):  # вызывается при смене геопозиции у инициализированного пользователя
        self.content[str(id)]['longitude'] = longitude
        self.content[str(id)]["latitude"] = latitude
        self.content[str(id)]["utc"] = 3
        print(self.content)

    # def __str__(self):  # строковое

    def havegeo(self, id):  # проверка наличия геопозиции у пользователя ID
        return self.content[str(id)]['latitude']

    def to_notify(self, id):
        return self.content[str(id)]['notifications']

    def get_info(self):
        return self.content

    def turn_nots(self, id):
        self.content[str(id)]['notifications'] = not self.content[str(id)]['notifications']


db = DataBase()  # создание объекта базы данных


@bot.message_handler(commands=["start"])
def start(message): # инициализация пользователя, отправляет приветствие и запрашивает геопозицию
    try:
        db.new_obj(id=message.chat.id,  # пользователь записывается в БД
                   name=message.from_user.first_name)
        bot.send_message(message.chat.id, f'Здравствуй, {db[message.chat.id]["name"]}!'
                                          f' Это бот для получения прогноза погоды '
                                          f'по твоей геопозиции. Отправь мне свою локацию!')
    except Exception as e:
        bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


@bot.message_handler(content_types=['location'])
def get_location(message):  # функция вызывается, когда пользователь отсылает своб геопозицию
    try:
        if db.havegeo(message.chat.id):  # проверка, есть ли геопозиция пользователя в базе данных
            bot.send_message(message.chat.id, f'Поменял вашу геопозицию!\n'  
                                              f'Старые данные:'
                                              f' долгота {str(db[message.chat.id]["longitude"])}'
                                              f' широта {str(db[message.chat.id]["latitude"])}'
                                              f'\nНовые данные: '
                                              f'долгота {str(message.location.longitude)}'
                                              f' широта {str(message.location.latitude)}'
                                              f'\nЧтобы получить прогноз, пришлите любой символ')
            db.change_loc(id=message.chat.id,  # если да, то новая геопозиция записывается в базу данных
                          latitude=message.location.latitude,
                          longitude=message.location.longitude)
        else:
            db.new_obj(id=message.chat.id,  # если нет, то создается новый объект и туда записываются координаты пользователя
                       name=message.from_user.first_name,
                       latitude=message.location.latitude,
                       longitude=message.location.longitude)
            bot.send_message(message.chat.id, f'Сохранил вашу геопозицию!'
                                              f' Для получения прогроза погоды, отправьте любой символ.'
                                              f' \n   Сменить геопозицию: /start')
    except Exception as e:
        bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


@bot.message_handler()
def give_response(message):  # отправка сообщения с прогнозом погоды, вызывается при получении любого сообщения кроме /start и геопозиции
    try:
        headers = {'X-Gismeteo-Token': '61f2622d432a64.10698954'}
        _latitude = db[message.chat.id]['latitude']
        _longitude = db[message.chat.id]['longitude']
        print(_longitude)
        print(_latitude)
        url = f'https://api.gismeteo.net/v2/weather/current/?latitude={_latitude}&longitude={_longitude}'
        # запрос отправляется в gismeteo API
        resp = requests.get(url, headers=headers).json()
        print(resp)
        bot.send_message(message.chat.id, parce(resp))  # запрос преобразуется в сообщение, отправляется пользователю
    except Exception as e:
        bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


@bot.message_handler(commands=['notifications'])
def change_nots(message):
    try:
        db.turn_nots(id=message.chat.id)
        bot.send_message(message.chat.id, f'Теперь уведомления'
                                          f' {"включены." if db[str(message.chat.id)]["notifications"] else "выключены."}')
    except Exception as e:
        bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)

def parce(jsonfile):  # функция преобразует ответ на  запрос .json в строку, которая является прогнозом погоды
    try:
        global weather_code
        return f"{'Ожидается' if jsonfile['response']['kind'] == 'Frc' else 'Наблюдается'}" \
               f" следующая погода:\n" \
               f"{jsonfile['response']['description']['full']}.\n" \
               f"Температура: {str(jsonfile['response']['temperature']['air']['C'])}" \
               f", (ощущается как) {str(jsonfile['response']['temperature']['comfort']['C'])}, " \
               f"температура воды {str(jsonfile['response']['temperature']['water']['C'])}." \
               f"\nВлажность: {str(jsonfile['response']['humidity']['percent'])}%\n" \
               f"Атмосферное давление: {str(jsonfile['response']['pressure']['mm_hg_atm'])} мм ртутного столба\n" \
               f"Облачность: {str(jsonfile['response']['cloudiness']['percent'])}%\n" \
               f"Вероятность грозы {'есть.' if jsonfile['response']['storm'] else 'отсутствует.'}\n" \
               f"Осадки: " \
               f"{['осадков нет.', 'дождь', 'снег', 'нет осадков'][jsonfile['response']['precipitation']['type']]}\n" \
               + (('Погодное явление: ' + weather_code[str(jsonfile['response']['phenomenon'])]
                   if str(jsonfile['response']['phenomenon']) in weather_code.keys() else '') if
                  'phenomenon' in jsonfile['response'].keys() else '')
    except Exception as e:
        print(e)


class ScheduleMessage:
    @staticmethod
    def try_send_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)

    @staticmethod
    def start_process():
        p1 = Process(target=ScheduleMessage.try_send_schedule,
                     args=())
        p1.start()


def notice():
    print(db)
    try:
        database = db.get_info()
        print(database)
        database = db.content
        print(database)
        for _id in database:
            print(_id, database[_id])
            try:
                send_not(database[_id], _id)
            except KeyError as e:
                print(e)

    except Exception as e:
        print(e)


def start_sch():
    try:
        schedule.every().day.at('13:28').do(notice)
        schedule.every().day.at('18:00').do(notice)
    except Exception as e:
        print(e)


@bot.message_handler()
def send_not(database, _id):
    print(234)
    try:
        if database['notifications']:
            headers = {'X-Gismeteo-Token': '61f2622d432a64.10698954'}
            _latitude = db[_id]['latitude']
            _longitude = db[_id]['longitude']
            print(_longitude)
            print(_latitude)
            url = f'https://api.gismeteo.net/v2/weather/current/?latitude={_latitude}&longitude={_longitude}'
            # запрос отправляется в gismeteo API
            resp = requests.get(url, headers=headers).json()
            bot.send_message(_id, parce(resp))  # запрос преобразуется в сообщение, отправляется пользователю
    except Exception as e:
        bot.send_message(_id, f'ERROR: {e}')
        print(e)


if __name__ == '__main__':  # запуск бота  через интерпретатор
    print('Starting..')
    ScheduleMessage.start_process()
    start_sch()
    bot.polling(none_stop=True, interval=1)