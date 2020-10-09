import requests
from datetime import datetime
import os.path

from bs4 import BeautifulSoup
import cv2

from db import Weather


class WeatherMaker:
    def get_weather(self):
        result = []
        response = requests.get('https://yandex.ru/pogoda/nizhny-novgorod')

        if response.status_code == 200:
            html_doc = BeautifulSoup(response.text, features='html.parser')
            forecast = html_doc.find_all(
                'div', {'class': 'forecast-briefly__days'})
            forecast_days = forecast[0].find_all(
                'div', {'class': 'forecast-briefly__day'})
            for item in forecast_days:
                day_temperature = item.find_all(
                    'div', {'class': 'forecast-briefly__temp_day'})
                temperature = day_temperature[0].find_all(
                    'span', {'class': 'temp__value'})
                datestr = item.find_all(
                    'time', {'class': 'time forecast-briefly__date'})
                condition = item.find_all(
                    'div', {'class': 'forecast-briefly__condition'})
                day = datetime.strptime(
                    datestr[0]['datetime'].split()[0], '%Y-%m-%d')
                data = {
                    'date': day,
                    'temperature': temperature[0].text,
                    'condition': condition[0].text
                }
                result.append(data)
            return result


class ImageMaker:
    WHITE = (255, 255, 255)
    YELLOW = (0, 255, 255)
    BLUE = (255, 0, 0)
    CYAN = (255, 255, 0)
    GREY = (128, 128, 128)

    def __init__(self, input_dir):
        self.weather = {}
        self.input_dir = input_dir
        self.template = cv2.imread(os.path.join(input_dir, 'probe.jpg'))

        self.output = self.template.copy()

    @staticmethod
    def viewImage(image, name_of_window):
        cv2.namedWindow(name_of_window, cv2.WINDOW_NORMAL)
        cv2.imshow(name_of_window, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def make_postcard(self, weather):
        self.weather = weather
        if weather['condition'] in ('Дождь', 'Ливень'):
            self._make_postcard_template(
                'Rainy', 'rain.png', 'piglet.png', self.BLUE)
        elif weather['condition'] in ('Облачно с прояснениями', 'Облачно'):
            self._make_postcard_template(
                'Cloudy', 'cloud.png', 'edward.png', self.GREY)
        elif weather['condition'] in ('Малооблачно', 'Ясно'):
            self._make_postcard_template(
                'Clear', 'sun.png', 'solaire.png', self.YELLOW)
        elif weather['condition'] in ('Снег',):
            self._make_postcard_template(
                'Snow', 'snow.png', 'fargo.png', self.CYAN)

    def _overlay_image(self, img, top, left):
        rows, cols, channels = img.shape
        roi = self.output[top:rows + top, left:cols + left]

        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, mask = cv2.threshold(img_gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)

        bg = cv2.bitwise_and(roi, roi, mask=mask_inv)

        img_fg = cv2.bitwise_and(img, img, mask=mask)

        dst = cv2.add(bg, img_fg)
        self.output[top:rows + top, left:cols + left] = dst

    def _draw_gradient(self, color):
        rows = self.output.shape[0]
        for row in range(rows):
            b = 255 - (255 - color[0]) * (row / rows)
            g = 255 - (255 - color[1]) * (row / rows)
            r = 255 - (255 - color[2]) * (row / rows)
            cv2.line(
                self.output, (0, row), (self.output.shape[1], row), (b, g, r), 1)

    def _make_postcard_template(self, condition, weather_symbol, picture, color):
        text = self.weather['date'].strftime('%d %B')
        if text[0] == '0':
            text = text[1:]
        symbol = cv2.imread(os.path.join(self.input_dir, weather_symbol))
        character = cv2.imread(os.path.join(self.input_dir, picture))
        char_x = self.output.shape[1] - character.shape[1]
        char_y = self.output.shape[0] - character.shape[0]

        self._draw_gradient(color)
        self._overlay_image(symbol, 175, 30)
        self._overlay_image(character, char_y, char_x)
        cv2.putText(self.output, text, (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
        cv2.putText(self.output, self.weather['temperature'],
                    (250, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
        cv2.putText(self.output, condition, (150, 220),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
        os.makedirs('postcards', exist_ok=True)
        path = os.path.join('postcards', self.weather['date'].strftime('%d-%m-%Y') + '.jpg')
        cv2.imwrite(path, self.output)


class DatabaseUpdater:
    def save_data(self, data):
        day = data['date']
        temp = data['temperature']
        cond = data['condition']
        new_data = Weather.replace(date=day, temperature=temp, condition=cond).execute()

    def get_data(self, day1, day2):
        result = []
        for weather in Weather.select().where(Weather.date.between(day1, day2)):
            result.append({
                'date': weather.date,
                'temperature': weather.temperature,
                'condition': weather.condition
            })
        return result


if __name__ == '__main__':
    weathermaker = WeatherMaker()
    database = DatabaseUpdater()
    imagemaker = ImageMaker('assets')
    weathermaker.get_weather()
    data = database.get_data(datetime(2020, 7, 2), datetime(2020, 7, 10))
    imagemaker.make_postcard(data[0])
