# -*- coding: utf-8 -*-

import datetime as dt


def now(delta_hours: int = 0):
    """ Возвращает текущие дату и время со смещением на разницу во времени
        delta_hours: int
    """
    return dt.datetime.today() + dt.timedelta(hours=delta_hours)


class Transport:
    """ Класс для транспорта
        Может сравниваться сам с собой и с классом datetime.datetime
    """
    def __init__(self, departure_time: list, arrival_time: list,
                 direction: str, transport_type):
        """ Принимает на вход обязательные параметры:

            departure_time: list – время отправления
            arrival_time: list – время прибытия
            direction: str – направление движения
            transport_type – тип транспорта (Bus или Suburban)
        """
        self.departure_time = self.list_to_datetime(departure_time)
        self.arrival_time = self.list_to_datetime(arrival_time)
        self.direction = direction
        self.transport_type = transport_type

    @staticmethod
    def list_to_datetime(time: list):
        """ Принимает на вход обязательный параметр time: list – список, в
            котором хранятся часы и минуты, возвращает дату и время в формате
            datetime.datetime
        """
        datetime = dt.datetime(year=now().year,
                               month=now().month,
                               day=now().day,
                               hour=time[0],
                               minute=time[1])
        if time[0] in (0, 1, 2):
            datetime += dt.timedelta(days=1)
        return datetime

    def __repr__(self):
        """ Перегрузка стандартного оператора: показывает формальное строковое
            представление класса
        """
        return f'{self.transport_type}(departure_time={self.departure_time}, '\
               f'arrival_time={self.arrival_time}, direction={self.direction})'

    def __len__(self):
        """ Перегрузка стандартного оператора: возвращает длину формального
            строкового представления класса __repr__() для последующего
            выведения колонки на экран
        """
        return len(self.__repr__())

    def __add__(self, other):
        if isinstance(other, str):
            return self.__str__() + other

    def __radd__(self, other):
        if isinstance(other, str):
            return other + self.__str__()

    def __hash__(self):
        departure_value = self.departure_time.minute % \
                          (self.departure_time.hour + 1)
        arrival_value = self.arrival_time.minute % (self.arrival_time.hour + 1)
        multiplier = (len(self.direction) - len(self.transport_type))
        to_hash = (departure_value * arrival_value +
                   arrival_value * departure_value) * multiplier
        return to_hash

    def __lt__(self, other):
        if isinstance(other, Transport):
            return self.departure_time < other.departure_time
        elif isinstance(other, dt.datetime):
            return self.departure_time < other

    def __le__(self, other):
        if isinstance(other, Transport):
            return self.departure_time <= other.departure_time
        elif isinstance(other, dt.datetime):
            return self.departure_time <= other

    def __eq__(self, other):
        if isinstance(other, Transport):
            return self.departure_time == other.departure_time
        elif isinstance(other, dt.datetime):
            return self.departure_time == other

    def __ne__(self, other):
        if isinstance(other, Transport):
            return self.departure_time != other.departure_time
        elif isinstance(other, dt.datetime):
            return self.departure_time != other

    def __gt__(self, other):
        if isinstance(other, Transport):
            return self.departure_time > other.departure_time
        elif isinstance(other, dt.datetime):
            return self.departure_time > other

    def __ge__(self, other):
        if isinstance(other, Transport):
            return self.departure_time >= other.departure_time
        elif isinstance(other, dt.datetime):
            return self.departure_time >= other


class CurriculumColumn:
    """ Класс для колонок, в которых хранятся ячейки класса Transport
        Итерируемый: при итерации возвращает последовательно ячейки
    """
    def __init__(self, column: dict):
        """ Принимает на вход словарь колонки column: dict с 1 ключом – именем
            колонки, и списком из ячеек колонки класса Transport
        """
        self.name = tuple(column.keys())[0]
        self.data = tuple(column.values())[0]
        self.index = len(self)
        self.max_len = self.find_max_len(self.data)

    def __len__(self):
        """ Возвращает длину списка ячеек – количество ячеек класса Transport
            в колонке
        """
        return len(self.data)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index > 0:
            i = len(self) - self.index
            self.index -= 1
            return self.data[i]
        elif self.index == 0:
            self.index = len(self)
            raise StopIteration

    def __str__(self):
        str_separator = '\n|' + '-' * self.max_len + '|\n'
        to_center = (self.max_len - len(self.name)) // 2
        to_return = ' ' * to_center + self.name + str_separator
        for transport in self.data:
            to_return += f'|{repr(transport)}| {str_separator}'
        return to_return

    @staticmethod
    def find_max_len(transports: list):
        """ Принимает на вход список ячеек transports: list, в котором хранятся
            объекты класса Transport, и возвращает максимальную длину
            формального строкового представления __repr__() среди всех ячеек
            для того, чтобы можно было вывести колонку в консоль
        """
        max_len = 0
        for transport in transports:
            if len(transport) > max_len:
                max_len = len(transport)
        return max_len


class CurriculumPage:
    """ Класс для страниц, которые состоят из колонок
        Итерируемый: при итерации возвращает последовательно колонки
        Можно обращаться к колонокам по ключам – их именам
    """
    def __init__(self, columns: dict):
        """ Принимает на вход словарь columns с 1 ключом, который является
            именем страницы CurriculumPage, значением выступает список из
            колонок CurriculumColumn
        """
        self.name = tuple(columns.keys())[0]
        self.columns = dict()
        self.columns_order = list()
        for column in columns[self.name]:
            self.columns_order.append(column.name)
            self.columns[column.name] = column
        self.index = len(self)

    def __len__(self):
        """ Возвращает длину списка колонок – количество колонок класса
            CurriculumColumn в странице
        """
        return len(self.columns)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index > 0:
            i = len(self) - self.index
            self.index -= 1
            return self.columns_order[i]
        elif self.index == 0:
            self.index = len(self)
            raise StopIteration

    def __getitem__(self, key):
        return self.columns[key]


class Curriculum:
    """ Класс для расписания, которое состоит из страниц
        Итерируемый: при итерации возвращает последовательно страницы
        Можно обращаться к страницам по ключам – их именам
    """
    def __init__(self, pages: dict):
        """ Принимает на вход словарь pages с 1 ключом, который является
            именем расписания Curriculum, значением выступает список из
            страниц CurriculumPage
        """
        self.name = tuple(pages.keys())[0]
        self.pages = dict()
        self.pages_order = list()
        for page in pages[self.name]:
            self.pages_order.append(page.name)
            self.pages[page.name] = page
        self.index = len(self)

    def __len__(self):
        """ Возвращает длину списка страниц – количество страниц класса
            CurriculumPage в расписании
        """
        return len(self.pages)

    def __iter__(self):
        return self

    def __next__(self):
        if self.index > 0:
            i = len(self) - self.index
            self.index -= 1
            return self.pages_order[i]
        elif self.index == 0:
            self.index = len(self)
            raise StopIteration

    def __getitem__(self, key):
        return self.pages[key]
