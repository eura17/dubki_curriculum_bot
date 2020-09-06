# -*- coding: utf-8 -*-

import os
import re
import datetime as dt
import json
from urllib.request import urlretrieve as download, urlopen
from fitz import open as open_pdf
from bs4 import BeautifulSoup
from transports import Bus, Suburban
from abstractions import now, CurriculumColumn, CurriculumPage, Curriculum


class BusesCurriculum(Curriculum):
    """ Класс для расписания автобусов и работы с ним
    """
    def __init__(self, filename: str = 'Расписание.pdf'):
        """ Принимает на вход название файла filename: str, в котором будет
            будет храниться pdf-файл с расписанием автобусов и создает объект
            класса Curriculum
        """
        self.filename = filename
        super().__init__(self.create_curriculum())

    def create_curriculum(self):
        """ Создает расписание автобусов класса Curriculum
        """
        self.get_curriculum_pdf()
        curriculum_pdf = open_pdf(self.filename)
        weekdays = iter(('weekday','saturday', 'sunday'))
        pages = []
        is_first_page = True
        for page_pdf in curriculum_pdf:
            hours_of_previous_block = 0
            if not is_first_page:
                pages.append(self.create_page(buses_for_day, current_weekday))
            current_weekday = next(weekdays)
            buses_for_day = []
            for block in page_pdf.getText('blocks'):
                hours_of_current_block, buses = self.\
                    get_buses_from_block(block, current_weekday)
                if hours_of_current_block is None:  # net avtobusov
                    continue
                if self.is_next_weekday(hours_of_current_block,
                                        hours_of_previous_block):
                    pages.append(self.create_page(buses_for_day,
                                                  current_weekday))
                    current_weekday = next(weekdays)
                    buses_for_day = []
                buses_for_day += buses
                hours_of_previous_block = hours_of_current_block
            is_first_page = not is_first_page
        pages.append(self.create_page(buses_for_day, current_weekday))
        return {'Расписание автобусов': pages}

    def get_curriculum_pdf(self):
        """ Находит ссылку на pdf-файл с расписанием автобусов из кнопки в
            паблике Дубков Вконтакте
        """
        link_to_dubki_group = 'https://vk.com/dubki'
        soup = BeautifulSoup(urlopen(link_to_dubki_group),
                             features='html.parser')
        for a_with_href in soup.find_all('a', href=True):
            if 'Расписание' in str(a_with_href):
                link_to_pdf = a_with_href['href']
                download(link_to_pdf, filename=self.filename)
                break

    def get_buses_from_block(self, block: list, current_weekday: str):
        """ Принимает на вход обязательные параметры block: list – блок из
            pdf-файла с расписанием автобусов, проверяет этот блок, является
            ли он блоком с информацией об автобусе, и достает из него в этом
            случае все автобусы, и current_weekday: str – текущий день недели
            для составления расписания

            Возвращает часы первого автобуса в блоке и список всех автобусов
            из блока класса Bus (если блок не содержит автобусов, возвращает
            None, None)
        """
        block = block[4]
        hours_of_current_block, buses_times = self.clear_block(block)
        if hours_of_current_block is None:  # net avtobusov
            return None, None
        buses_from_block = []
        is_bus_for_dubki = True
        time_of_previous_dubki_bus = [0, 0]
        for bus_time in buses_times:
            if bus_time == 'прибыт.':
                continue
            elif bus_time == '----':
                is_bus_for_dubki = not is_bus_for_dubki
                continue
            bus, time_of_previous_dubki_bus = \
                self.create_bus(bus_time, is_bus_for_dubki,
                                time_of_previous_dubki_bus, current_weekday)
            buses_from_block.append(bus)
            is_bus_for_dubki = not is_bus_for_dubki
        return hours_of_current_block, buses_from_block

    def clear_block(self, block: str):
        """ Принимает на вход block: str и очищает его, если блок содержит
            информацию об автобусах

            Возвращает часы первого автобуса в блоке и список всех автобусов
            из блока с их временем (если блок не содержит информации об
            автобусах, возвращает None, None)
        """
        if self.is_bus_block(block):
            buses_times = block.split()
            hours_of_current_block = int(buses_times[0].split(':')[0])
            return hours_of_current_block, buses_times
        return None, None

    @staticmethod
    def is_bus_block(line: str):
        """ Принимает на вход строку line: str и проверяет, является ли она
            строкой, содержащей время автобусов
        """
        return not re.search(r'\d:\d\d', line) is None

    def create_bus(self, bus_time: str, is_bus_from_dubki: bool,
                   time_of_matched_dubki_bus: list, weekday: str):
        """ Принимает на вход время автобуса bus_time: str, логическую
            переменную is_bus_from_dubki: bool, отвечающую за информацию, идет
            ли автобусов из дубков или нет, время сопоставляемого
            автобуса time_of_matched_dubki_bus: list для того, чтобы можно
            было определить время отправления автобуса из одинцово, если он
            отправляется по прибытии, день недели для отправления weekday: str

            Возвращает автобус класса Bus и время отправления списком для
            обновления переменной time_of_matched_dubki_bus: list
        """
        bus_info = self.inspect_bus(bus_time, time_of_matched_dubki_bus)
        if bus_info[1]:
            direction = 'Дубки-Славянский бульвар' if is_bus_from_dubki \
                else 'Славянский бульвар-Дубки'
        else:
            direction = 'Дубки-Одинцово' if is_bus_from_dubki \
                else 'Одинцово-Дубки'
        bus = Bus(departure_time=bus_info[0],
                  direction=direction,
                  weekday=weekday,
                  is_slavyanka=bus_info[1],
                  is_accurate=bus_info[2])
        return bus, bus_info[0]

    def inspect_bus(self, bus_time: str, time_of_matched_dubki_bus: list):
        """ Принимает время автобуса bus_time: str и время сопоставляемого
            автобуса time_of_matched_dubki_bus: list для того, чтобы можно
            было определить время отправления автобуса из одинцово, если он
            отправляется по прибытии и оценивает автобус
            
            Возвращает всю информацию по автобусу: время отправления 
            departure_time: list, является ли автобус славянкой 
            is_slavyanka: bool, точное ли время отправления is_accurate: bool
        """
        is_slavyanka, bus_time = self.is_slavyanka(bus_time)
        is_accurate, bus_time = self.is_accurate(bus_time)
        if is_accurate:
            departure_time = list(map(int, bus_time.split(':')))
        else:
            departure_time = time_of_matched_dubki_bus
        return departure_time, is_slavyanka, is_accurate

    @staticmethod
    def is_slavyanka(bus: str):
        """ Принимает автобус и оценивает, является ли автобус славянкой
        """
        if '*' in bus:
            bus = bus.replace('*', '').replace('*', '')
            return True, bus
        return False, bus

    @staticmethod
    def is_accurate(bus: str):
        """ Принимает автобус и оценивает, точное ли время отправления у
            автобуса
        """
        return not bus == 'по', bus

    @staticmethod
    def is_next_weekday(hours_of_current_line: int,
                        hours_of_previous_line: int):
        """ Проверяет, закончилось ли расписание субботы
        """
        return hours_of_current_line < hours_of_previous_line

    @staticmethod
    def create_page(buses: list, weekday: str):
        """ Принимает на вход список из автобусов buses: list и день недели
            weekday: str

            Создает страницу класса CurriculumPage из колонок CurriculumColumn
        """
        buses_with_directions = {'Дубки-Одинцово': [],
                                 'Одинцово-Дубки': []}
        for bus in buses:
            if bus.direction == 'Дубки-Славянский бульвар':
                buses_with_directions['Дубки-Одинцово'].append(bus)
            elif bus.direction == 'Славянский бульвар-Дубки':
                buses_with_directions['Одинцово-Дубки'].append(bus)
            else:
                buses_with_directions[bus.direction].append(bus)
        buses_with_directions['Дубки-Одинцово'].sort()
        buses_with_directions['Одинцово-Дубки'].sort()
        dubki_odintsovo_column = CurriculumColumn(
            {'Дубки-Одинцово': buses_with_directions['Дубки-Одинцово']})
        odintsovo_dubki_column = CurriculumColumn(
            {'Одинцово-Дубки': buses_with_directions['Одинцово-Дубки']})
        page = CurriculumPage(
            {weekday: [dubki_odintsovo_column, odintsovo_dubki_column]})
        return page

    def get_buses_for_hour(self, direction: str):
        """ Находит автобусы на ближайший час
        """
        current_time = now()
        max_time = current_time + dt.timedelta(hours=1)
        weekday = self.define_weekday()
        relevant_buses = []
        for bus in self[weekday][direction]:
            if current_time <= bus <= max_time:
                relevant_buses.append(bus)
        return relevant_buses

    def get_slavyanki(self, direction: str):
        """ Находит славянки на весь день
        """
        current_time = now()
        weekday = self.define_weekday()
        relevant_buses = []
        for bus in self[weekday][direction]:
            if bus.is_slavyanka and bus >= current_time:
                relevant_buses.append(bus)
        return relevant_buses

    @staticmethod
    def define_weekday():
        """ Определяет день недели для использования расписания: где искать
            автобусы на сегодня
        """
        today = now().isoweekday()
        hour = now().hour
        if today in (1, 2, 3, 4, 5) or today == 5 and hour in (0, 1, 2):
            return 'weekday'
        elif today == 6 or today == 6 and hour in (0, 1, 2):
            return 'saturday'
        elif today == 7 or today == 7 and hour in (0, 1, 2):
            return 'sunday'


class SuburbansCurriculum(Curriculum):
    """ Класс для расписания электричек и работы с ним
    """
    def __init__(self):
        """ Инициализирует объект класса класса Curriculum с расписанием
            электричек
        """
        super().__init__(self.create_curriculum())

    def create_curriculum(self):
        """ Создает расписание электричек класса Curriculum
        """
        weekdays = iter(('today', 'tomorrow'))
        pages = []
        stations = ('Кунцево', 'Славянский бульвар', 'Фили', 'Беговая', 'Белорусский вокзал')
        for next_day in False, True:
            suburbans_for_day = []
            current_weekday = next(weekdays)
            for is_from_odintsovo in (True, False):
                for station in stations:
                    from_to = f'Одинцово-{station}' if is_from_odintsovo \
                        else f'{station}-Одинцово'
                    suburbans = self.get_suburbans(station, from_to,
                                                   is_from_odintsovo, next_day)
                    suburbans_for_day.append(suburbans)
            pages.append(self.create_page(suburbans_for_day, current_weekday))
        return {'Расписание автобусов': pages}

    def get_suburbans(self, station: str, direction: str,
                      is_from_odintsovo: bool, next_day: bool):
        """ Принимает на вход название станции station: str, направление
            движения direction: str, информацией, направляется ли электричка
            из одинцово или нет is_from_odintsovo: bool, информацией, нужно ли
            искать расписание на следующий день

            Возвращает список электричек, отправляющих по направлению direction
            со станции или на станцию
        """
        json_suburbans = self.make_request(station, is_from_odintsovo,
                                           next_day)
        suburbans = []
        if 'error' not in json_suburbans:
            suburbans_segments = json_suburbans['segments']
            for suburban in suburbans_segments:
                suburban = self.create_suburban(suburban, direction, next_day)
                suburbans.append(suburban)
        return suburbans

    @staticmethod
    def make_request(station: str, is_from_odintsovo: bool,
                     next_day: bool):
        """ Принимает на вход название станции station: str, информацией,
            направляется ли электричка из одинцово или нет
            is_from_odintsovo: bool, информацией, нужно ли искать расписание
            на следующий день

            Возвращает поезда в формате json
        """
        stations = {'Одинцово': 'c10743',
                    'Кунцево': 's9601728',
                    'Славянский бульвар': 's9876336',
                    'Фили': 's9600821',
                    'Беговая': 's9601666',
                    'Белорусский вокзал': 's2000006'}
        apikey = os.getenv('APIKEY_YANDEX')
        station_from = 'Одинцово' if is_from_odintsovo else station
        station_to = 'Одинцово' if not is_from_odintsovo else station
        today = now()
        if next_day:
            today += dt.timedelta(days=1)
        url = f'https://api.rasp.yandex.net/v3.0/search/?apikey={apikey}' \
              f'&from={stations[station_from]}&to={stations[station_to]}' \
              f'&date={now().date()}&format=json&limit=1000&lang=ru_RU&' \
              f'system=yandex&show_systems=yandex'
        response = urlopen(url)
        data_from_response = response.read()
        encoding = response.info().get_content_charset('utf-8')
        json_data = json.loads(data_from_response.decode(encoding))
        return json_data

    @staticmethod
    def create_suburban(suburban_json: dict, direction: str, next_day: bool):
        """ Принимает информацию о поезде в формате json suburban_json: dict,
            направление движения direction: str и next_day: bool, поезд получен
            на следующий день или нет

            Создает и возвращает объект класса Suburban
        """
        begin_dt = suburban_json['departure'].find('T') + 1
        end_dt = suburban_json['departure'].find('T') + 6
        departure_time_raw = suburban_json['departure'][begin_dt:end_dt]
        departure_time = list(map(int, departure_time_raw.split(':')))
        begin_at = suburban_json['arrival'].find('T') + 1
        end_at = suburban_json['arrival'].find('T') + 6
        arrival_time_raw = suburban_json['arrival'][begin_at:end_at]
        arrival_time = list(map(int, arrival_time_raw.split(':')))
        suburban_name = suburban_json['thread']['title']
        suburban_type = suburban_json['thread']['transport_subtype']['code']
        suburban = Suburban(departure_time=departure_time,
                            arrival_time=arrival_time,
                            direction=direction,
                            suburban_name=suburban_name,
                            suburban_type=suburban_type,
                            next_day=next_day)
        return suburban

    @staticmethod
    def create_page(suburbans_for_day: list, weekday: str):
        """ Принимаем список из электричек suburbans_for_day: list на весь
            день weekday: str

            Создает страницу класса CurriculumPage из колонок CurriculumColumn
        """
        suburbans_with_directions = {}
        for suburbans_for_station in suburbans_for_day:
            suburbans_for_station.sort()
            direction = suburbans_for_station[0].direction
            suburbans_with_directions[direction] = []
            for suburban in suburbans_for_station:
                suburbans_with_directions[direction].append(suburban)
        suburbans_columns = []
        for direction in suburbans_with_directions:
            suburbans_column = CurriculumColumn(
                {direction: suburbans_with_directions[direction]})
            suburbans_columns.append(suburbans_column)
        page = CurriculumPage({weekday: suburbans_columns})
        return page

    def get_suburbans_for_hour(self, direction: str):
        """ Находит электрички на ближайший час
        """
        current_time = now()
        max_time = current_time + dt.timedelta(hours=1)
        current_weekdays = self.define_weekday()
        relevant_suburbans = []
        for weekday in current_weekdays:
            for suburban in self[weekday][direction]:
                if current_time <= suburban <= max_time:
                    if not self.is_suburban_already_exists(suburban,
                                                           relevant_suburbans):
                        relevant_suburbans.append(suburban)
        return relevant_suburbans

    @staticmethod
    def define_weekday():
        """ Определяет день недели для использования расписания: стоит ли
            искать электрички среди тех, которые находятся на следующий день
        """
        today = now().isoweekday()
        today_plus_1_hour = (now() + dt.timedelta(hours=1)).isoweekday()
        if today_plus_1_hour - today == 0:
            return 'today',
        return 'today', 'tomorrow'

    def is_suburban_already_exists(self, suburban: Suburban, suburbans: list):
        already_exists = False
        for already_exists_suburban in suburbans:
            if already_exists_suburban == suburban:
                already_exists = True
                break
        return already_exists
