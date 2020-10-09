from datetime import datetime, timedelta
import re

from weathermaker import WeatherMaker, ImageMaker, DatabaseUpdater


class WeatherCards:
    def __init__(self):
        self.forecast = []
        self.weather_engine = WeatherMaker()
        self.image_engine = ImageMaker('assets')
        self.db_engine = DatabaseUpdater()

    def run(self):
        data = self.weather_engine.get_weather()
        for item in data:
            self.db_engine.save_data(item)
        today = datetime.today()
        week_ago = today - timedelta(days=7)
        self.forecast = self.db_engine.get_data(week_ago, today)

        while True:
            print('Доступные действия:')
            print('1. Получить прогнозы за диапазон дат')
            print('2. Вывести прогнозы на консоль')
            print('3. Создать открытки из полученных прогнозов')
            print('4. Завершить программу\n')
            while True:
                choice = input('Выберите действие: ')
                if not re.match(r'[1-4]', choice):
                    print('Я вас не понимаю')
                else:
                    break
            if choice == '1':
                self.get_forecast()
            elif choice == '2':
                self.print_forecast()
            elif choice == '3':
                self.make_cards()
            else:
                break

    def print_forecast(self):
        print('Полученные прогнозы:')
        for item in self.forecast:
            print(item['date'].strftime('%d.%m.%Y'),
                  item['temperature'], item['condition'])
        print()

    def get_forecast(self):
        while True:
            begin_date = input('Введите первую дату в формате "дд.мм.гггг": ')
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', begin_date):
                print('Я вас не понимаю')
            else:
                break
        while True:
            end_date = input('Введите вторую дату в формате "дд.мм.гггг": ')
            if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', end_date):
                print('Я вас не понимаю')
            else:
                break
        self.forecast = self.db_engine.get_data(
            datetime.strptime(begin_date, '%d.%m.%Y'),
            datetime.strptime(end_date, '%d.%m.%Y'))
        print('Прогнозы получены\n')

    def make_cards(self):
        for item in self.forecast:
            self.image_engine.make_postcard(item)


if __name__ == '__main__':
    program = WeatherCards()
    program.run()
