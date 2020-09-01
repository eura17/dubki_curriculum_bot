# -*- coding: utf-8 -*-

from setup import Config
from abstractions import now


class Answers:
    """ Класс для ответов бота на команды
    """
    def __init__(self):
        """ При инициализации запускает класс Config, отвечающий за настройку
            бота
        """
        self.config = Config()

    @staticmethod
    def start_answer():
        """ Ответ бота на стартовое сообщение по команде /start, приветственное
            сообщение
        """
        answer = '''Привет, дубчанин!
Я бот, с помощью которого ты сможешь узнать расписание ближайших автобусов.
Да, тебе не придется лезть в группу в ВК, я сделаю это за тебя.
А еще покажу расписание ближайших электричек.
Инструкция по работе /help'''
        return answer

    @staticmethod
    def help_answer():
        answer = '''
Управляй мной с помощью /menu или команд, если хочешь :)
Доступные команды:
/buses – список автобусов на ближайший час
/slavyanki – список славянок на сегодня
/suburbans (/trains) – список электричек на ближайший час
/file – PDF-файл с расписанием
/menu – главное меню бота'''
        return answer

    def buses_answer(self, direction: str):
        """ Принимает на вход направление движения автобусов direction: str и
            создает ответ бота на команду /buses, возвращает этот ответ и
            список автобусов
        """
        buses = self.config.buses_curriculum.get_buses_for_hour(direction)
        if len(buses) == 0:
            answer = 'К сожалению, автобусов в ближайший час нет :('
        else:
            grammar = {'Дубки-Одинцово': 'Автобусы от Дубков до Одинцово:\n',
                       'Одинцово-Дубки': 'Автобусы от Одинцово до Дубков:\n'}
            answer = grammar[direction]
            for bus in buses:
                answer += bus + self.count_delta(bus) + '\n'
        return answer, buses

    @staticmethod
    def count_delta(transport):
        """ Принимает на вход объект класса Transport, считает, через сколько
            он приедет и строит грамматически верное словосочетание, возвращает
            словосочетание
        """
        today = now()
        delta = abs((today.hour * 60 + today.minute) -
                    (transport.departure_time.hour * 60 +
                     transport.departure_time.minute))
        if delta > 60:
            delta = 60 - delta % 60
        if delta == 0:
            return ' – сейчас'
        elif delta == 60:
            add_delta = '1 час'
        elif 11 <= delta <= 19:
            add_delta = f'{delta} минут'
        elif delta % 10 == 1:
            add_delta = f'{delta} минуту'
        elif delta % 10 in [2, 3, 4]:
            add_delta = f'{delta} минуты'
        elif delta % 10 in [5, 6, 7, 8, 9, 0]:
            add_delta = f'{delta} минут'
        txt_delta = f' – через {add_delta}'
        return txt_delta

    def buses_after_suburbans_answer(self, suburbans: list):
        """ Принимает на вход список электричек suburbans: list и создает
            ответ бота с удобные пересадками с электричек на автобусы
        """
        direction = self.define_buses_direction_by_suburbans(suburbans)
        buses = self.config.buses_curriculum.get_buses_for_hour(direction)
        if len(buses) == 0:
            answer = 'К сожалению, удобных пересадок на автобусы ' \
                     'в ближайший час нет :('
        else:
            grammar = \
                {'Дубки-Одинцово':
                 'Удобные пересадки на автобусы от Дубков до Одинцово:\n',
                 'Одинцово-Дубки':
                     'Удобные пересадки на автобусы от Одинцово до Дубков:\n'}
            answer = grammar[direction]
            grammar_preposition = {'Дубки-Одинцово':
                                   'можно успеть на электрички: ',
                                   'Одинцово-Дубки':
                                   'можно успеть с электричек: '}
            buses_with_suburbans = self.link_suburbans_with_buses(
                buses, suburbans, direction)
            for bus in buses:
                if len(buses_with_suburbans[bus]) > 0:
                    answer += bus + self.count_delta(bus) + '\n'
                    txt_suburbans = grammar_preposition[direction]
                    for suburban in buses_with_suburbans[bus]:
                        suburban_time = suburban.departure_time.\
                            strftime('%H:%M')
                        txt_suburbans += f'в {suburban_time}, '
                    answer += txt_suburbans[:-2] + '\n'
        return answer

    @staticmethod
    def define_buses_direction_by_suburbans(suburbans: list):
        """ Принимает на вход список электричек на час suburbans: list и
            определяет, по какому направлению необходимо подобрать автобусы,
            возвращает направление автобусов
        """
        direction = suburbans[0].direction.split('-')
        if direction[0] == 'Одинцово':
            return 'Дубки-Одинцово'
        elif direction[1] == 'Одинцово':
            return 'Одинцово-Дубки'

    @staticmethod
    def link_suburbans_with_buses(buses: list, suburbans: list,
                                  direction: str):
        """ Принимает на вход список автобусов buses: list, список электричек
            suburbans: list и направление движения автобусов direction: str и
            связывает подходящие автобусы для электричек, возвращает словарь,
            в котором ключами являются автобусы, а значениями списки из
            подходящих для пересадки электричек
        """
        suburbans_for_buses = {}
        for bus in buses:
            suburbans_for_buses[bus] = []
            if bus.is_slavyanka:
                continue
            for suburban in suburbans:
                if direction == 'Дубки-Одинцово':  # в Москву
                    if suburban.departure_time >= bus.arrival_time:
                        suburbans_for_buses[bus].append(suburban)
                elif direction == 'Одинцово-Дубки':  # из Москвы
                    if suburban.arrival_time <= bus.departure_time:
                        suburbans_for_buses[bus].append(suburban)
        return suburbans_for_buses

    def slavyanki_answer(self, direction: str):
        """ Принимает на вход направление движения автобусов direction: str и
            создает ответ бота на команду /slavyanki, возвращает этот ответ
        """
        slavyanki = self.config.buses_curriculum.get_slavyanki(direction)
        if len(slavyanki) == 0:
            answer = 'К сожалению, славянок в ближайший час нет :('
        else:
            grammar = {'Дубки-Одинцово':
                       'Автобусы от Дубков до Славянского бульвара:\n',
                       'Одинцово-Дубки':
                       'Автобусы от Славянского бульвара до Дубков:\n'}
            answer = grammar[direction]
            for slavyanka in slavyanki:
                answer += slavyanka + '\n'
        return answer

    def suburbans_answer(self, direction: str):
        """ Принимает на вход направление движения электричек direction: str и
            создает ответ бота на команду /suburbans, возвращает этот ответ и
            список электричек
        """
        suburbans = self.config.suburbans_curriculum.get_suburbans_for_hour(
            direction)
        if len(suburbans) == 0:
            answer = 'К сожалению, электричек в ближайший час нет :('
        else:
            grammar = {'Одинцово-Кунцево':
                       'Электрички от Одинцово до Кунцево:\n',
                       'Одинцово-Фили':
                       'Электрички от Одинцово до Филей:\n',
                       'Одинцово-Беговая':
                       'Электрички от Одинцово до Беговой:\n',
                       'Одинцово-Белорусский вокзал':
                       'Электрички от Одинцово до Белорусского вокзала:\n',
                       'Белорусский вокзал-Одинцово':
                       'Электрички от Белорусского возкала до Одинцово:\n',
                       'Беговая-Одинцово':
                       'Электрички от Беговой до Одинцово:\n',
                       'Фили-Одинцово':
                       'Электрички от Филей до Одинцово:\n',
                       'Кунцево-Одинцово':
                       'Электрички от Кунцево до Одинцово:\n'}
            answer = grammar[direction]
            for suburban in suburbans:
                answer += suburban + '\n'
        return answer, suburbans

    def suburbans_after_buses_answer(self, buses: list, direction: str):
        """ Принимает на вход список автобусов buses: list и направление
            движения электричек direction: str, создает ответ с удобными
            пересадками с автобусов на электрички
        """
        suburbans = self.config.suburbans_curriculum.get_suburbans_for_hour(
            direction)
        if len(suburbans) == 0:
            answer = 'К сожалению, удобных пересадок в ближайший час нет :('
        else:
            grammar = {'Одинцово-Кунцево':
                       'Электрички от Одинцово до Кунцево:\n',
                       'Одинцово-Славянский бульвар':
                       'Электрички от Одинцово до Славянского бульвара:\n',
                       'Одинцово-Фили':
                       'Электрички от Одинцово до Филей:\n',
                       'Одинцово-Беговая':
                       'Электрички от Одинцово до Беговой:\n',
                       'Одинцово-Белорусский вокзал':
                       'Электрички от Одинцово до Белорусского вокзала:\n',
                       'Белорусский вокзал-Одинцово':
                       'Электрички от Белорусского возкала до Одинцово:\n',
                       'Беговая-Одинцово':
                       'Электрички от Беговой до Одинцово:\n',
                       'Фили-Одинцово':
                       'Электрички от Филей до Одинцово:\n',
                       'Славянский бульвар-Одинцово':
                       'Электрички от Кунцево до Славянского бульвара:\n',
                       'Кунцево-Одинцово':
                       'Электрички от Кунцево до Одинцово:\n'}
            answer = grammar[direction]
            grammar_preposition = {'Дубки-Одинцово':
                                   'можно успеть c автобусов: ',
                                   'Одинцово-Дубки':
                                   'можно успеть на автобусы: '}
            direction_b = self.define_buses_direction_by_suburbans(suburbans)
            suburbans_with_buses = self.link_buses_with_suburbans(
                suburbans, buses, direction_b)
            for suburban in suburbans:
                if len(suburbans_with_buses[suburban]) > 0:
                    answer += suburban + '\n'
                    txt_buses = grammar_preposition[direction_b]
                    for bus in suburbans_with_buses[suburban]:
                        bus_time = bus.departure_time.strftime('%H:%M')
                        txt_buses += f'в {bus_time}, '
                    answer += txt_buses[:-2] + '\n'
        return answer

    @staticmethod
    def link_buses_with_suburbans(suburbans: list, buses: list,
                                  direction: str):
        """ Принимает на вход список электричек suburbans: list, список
            автобусов buses: list и направление движения автобусов
            direction: str и связывает подходящие автобусы для электричек,
            возвращает словарь, в котором ключами являются электрички, а
            значениями списки из подходящих для пересадки автобусы
        """
        buses_for_suburbans = {}
        for suburban in suburbans:
            buses_for_suburbans[suburban] = []
            for bus in buses:
                if bus.is_slavyanka:
                    continue
                if direction == 'Дубки-Одинцово':  # в Москву
                    if bus.arrival_time <= suburban.departure_time:
                        buses_for_suburbans[suburban].append(bus)
                elif direction == 'Одинцово-Дубки':  # из Москвы
                    if bus.departure_time >= suburban.arrival_time:
                        buses_for_suburbans[suburban].append(bus)
        return buses_for_suburbans

    def check_updates(self):
        """ Создает ответ на команду только для админа /check_updates с
            информацией о времени последнего обновления расписания
        """
        last_update = self.config.last_update_time.strftime('%H:%M %d.%m.%Y')
        answer = f'Последнее обновление расписания: *{last_update}*'
        return answer
