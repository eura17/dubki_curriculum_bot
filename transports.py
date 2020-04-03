# -*- coding: utf-8 -*-

import datetime as dt
from abstractions import Transport


class Bus(Transport):
    def __init__(self, departure_time: list,
                 direction: str, weekday: str,
                 is_slavyanka: bool = False, is_accurate: bool = True):
        self.is_accurate = is_accurate
        if not self.is_accurate:
            departure_time = self.count_plus_15_mins(departure_time)
        arrival_time = self.count_plus_15_mins(departure_time)
        self.is_slavyanka = is_slavyanka
        self.weekday = weekday
        super().__init__(departure_time, arrival_time,
                         direction, transport_type='Bus')

    def count_plus_15_mins(self, departure_time):
        departure_time = self.list_to_datetime(departure_time)
        arrival_time_corrected = departure_time + dt.timedelta(minutes=15)
        return [arrival_time_corrected.hour, arrival_time_corrected.minute]

    def __str__(self):
        to_print = '🚌 *{}*' if self.is_accurate else '🚌 по прибытии ~ *{}*'
        departure_time_to_print = self.departure_time.strftime('%H:%M')
        to_print = to_print.format(departure_time_to_print)
        to_print += ' (*славянка*)' if self.is_slavyanka else ''
        return to_print


class Suburban(Transport): 
    def __init__(self, departure_time: list, arrival_time: list,
                 direction: str,
                 suburban_name: str, suburban_type: str,
                 next_day: bool):
        super().__init__(departure_time, arrival_time,
                         direction, transport_type='Suburban')
        suburban_types = {'stdplus': 'Стандарт плюс',
                         'suburban': 'Обычная электричка',
                         'rex': 'Экспресс РЭКС',
                         'mcd1': 'Иволга',
                         'aerstd': 'Аэроэкспресс'}
        self.type = suburban_types[suburban_type]
        self.name = suburban_name

    def __str__(self):
        departure_time = self.departure_time.strftime('%H:%M')
        arrival_time = self.arrival_time.strftime('%H:%M')
        to_print = f'🚆 *{departure_time}* – {self.name} *({self.type})* ' \
                   f'~ *{arrival_time}*'
        return to_print
