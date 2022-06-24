from sys import getsizeof
import asyncio
import telebot.async_telebot
import aioschedule as schedule
import aiohttp
import datetime as dt
from config import tg_token as token
from config import gis_token
from config import weather_code
import pickle


bot = telebot.async_telebot.AsyncTeleBot(token)


class DataBase:
    def __init__(self):
        self.content = {}

    def new_obj(self, id, latitude=None, longitude=None, name=None, notifications=True):
        self.content[str(id)] = {'name': name,
                                 'latitude': latitude,
                                 'longitude': longitude,
                                 'notifications': notifications,
                                 'utc': 3}

    def __getitem__(self, item):
        try:
            print(self.content)
            return self.content[str(item)]
        except Exception as e:
            print(e, 'no id in db')

    def includes(self, id):
        return str(id) in self.content.keys()

    def change_loc(self, id, latitude=0, longitude=0):
        self.content[str(id)]['longitude'] = longitude
        self.content[str(id)]["latitude"] = latitude
        self.content[str(id)]["utc"] = 3
        print(self.content)

    def __str__(self):
        return str(self.content)

    def havegeo(self, id):
        return self.content[str(id)]['latitude']

    def to_notify(self, id):
        return self.content[str(id)]['notifications']

    def get_info(self):
        return self.content

    def turn_nots(self, id):
        self.content[str(id)]['notifications'] = not self.content[str(id)]['notifications']

    def set_utz(self, id):
        self.content[str(id)]['utc'] = self.content[str(id)]['longitude'] // 15

    def __sizeof__(self):
        try:
            return getsizeof(self.content)
        except Exception as e:
            print(e)

    def __getstate__(self):
        state = {'content': self.content}
        return state

    def __setstate__(self, state):
        self.content = state['content']


with open("file.pkl", "rb") as fp:
    print(1)
    db = pickle.load(fp)
    print(f'LOADED DB:::: {db}\n self.content: {db.content}\n\n')


@bot.message_handler(commands=["start"])
async def start(message):
    try:
        db.new_obj(id=message.chat.id,
                   name=message.from_user.first_name)
        await bot.send_message(message.chat.id, f'Здравствуй, {db[message.chat.id]["name"]}!'
                                                f' Это бот для получения прогноза погоды '
                                                f'по твоей геопозиции. Отправь мне свою локацию!')
    except Exception as e:
        await bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


@bot.message_handler(content_types=['location'])
async def get_location(message):
    try:
        if db.havegeo(message.chat.id):
            await bot.send_message(message.chat.id, f'Поменял вашу геопозицию!\n'
                                                    f'Старые данные:'
                                                    f' долгота {str(db[message.chat.id]["longitude"])}'
                                                    f' широта {str(db[message.chat.id]["latitude"])}'
                                                    f'\nНовые данные: '
                                                    f'долгота {str(message.location.longitude)}'
                                                    f' широта {str(message.location.latitude)}'
                                                    f'\nЧтобы получить прогноз, пришлите любой символ')
            db.change_loc(id=message.chat.id,
                          latitude=message.location.latitude,
                          longitude=message.location.longitude)
        else:
            db.new_obj(id=message.chat.id,
                       name=message.from_user.first_name,
                       latitude=message.location.latitude,
                       longitude=message.location.longitude)
            db.set_utz(message.chat.id)
            await bot.send_message(message.chat.id, f'Сохранил вашу геопозицию!'
                                                    f' Для получения прогроза погоды, отправьте любой символ.'
                                                    f' \n   Сменить геопозицию: /start')
    except Exception as e:
        await bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


@bot.message_handler()
async def give_response(message):
    try:
        headers = {'X-Gismeteo-Token': gis_token}
        _latitude = db[message.chat.id]['latitude']
        _longitude = db[message.chat.id]['longitude']
        print(_longitude)
        print(_latitude)
        async with aiohttp.ClientSession() as session:
            url = f'https://api.gismeteo.net/v2/weather/current/?latitude={_latitude}&longitude={_longitude}'
            async with session.get(url, headers=headers) as resp:
                resp = await resp.json()
                print(resp)
        await session.close()
        await bot.send_message(message.chat.id,
                               parce(resp))
    except Exception as e:
        await bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


@bot.message_handler(commands=['notifications'])
async def change_nots(message):
    try:
        db.turn_nots(id=message.chat.id)
        await bot.send_message(message.chat.id, f'Теперь уведомления'
                                                f' {"включены." if db[str(message.chat.id)]["notifications"] else "выключены."}')
    except Exception as e:
        await bot.send_message(message.chat.id, f'ERROR: {e}')
        print(e)


def parce(jsonfile):
    try:
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


async def try_send_schedule():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def notice():
    try:
        for _id in db.content.keys():
            try:
                await send_not(_id)
            except KeyError as e:
                print(e)

    except Exception as e:
        print(e)


async def start_sch():
    try:
        schedule.every().day.at('12:00').do(notice)
        schedule.every().day.at('14:00').do(notice)
        schedule.every().day.at('18:00').do(notice)
        schedule.every().minute.do(notice)
    except Exception as e:
        print(e)


async def check_time(_id):
    return True
    # info_about_user = db[str(_id)]
    # utc = info_about_user['longitude'] // 15
    # if dt.datetime.now().time().hour - 3 + utc in ['1', '15', '18']:
    #     return True
    # return False


async def send_not(_id):
    try:
        if db[str(_id)]['notifications'] and db[str(_id)]['longitude'] and check_time(_id):
            headers = {'X-Gismeteo-Token': gis_token}
            _latitude = db[_id]['latitude']
            _longitude = db[_id]['longitude']
            print(_longitude)
            print(_latitude)
            async with aiohttp.ClientSession() as session:
                url = f'https://api.gismeteo.net/v2/weather/current/?latitude={_latitude}&longitude={_longitude}'
                async with session.get(url, headers=headers) as resp:
                    resp = await resp.json()
                    print(resp)

            await bot.send_message(_id, f'Ваш рогноз погоды! \n{parce(resp)}')
    except Exception as e:
        await bot.send_message(_id, f'ERROR: {e}')
        print(e)


async def savestate():
    while True:
        with open("file.pkl", "wb") as fp:
            pickle.dump(db, fp)
            print(f'DB saved!\ndb: {db}\ndb.content: {db.content}')
        await asyncio.sleep(15)  # !!!!!! ЗИМЕНИТЬ НА 60/120/180/240/300/6000


async def main():
    await start_sch()
    await asyncio.gather(bot.polling(interval=1,
                                     non_stop=True,
                                     timeout=1000,
                                     request_timeout=1000),
                         try_send_schedule(),
                         savestate())


if __name__ == '__main__':
    asyncio.run(main())
