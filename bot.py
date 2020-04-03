# -*- coding: utf-8 -*-

import os
import telebot
from keyboard import KeyboardMenu
from answers import Answers

TOKEN = os.getenv('TOKEN')
ADMIN_ID = 281452837
BOT = telebot.TeleBot(TOKEN)
ANSWERS = Answers()
DATABASE = ANSWERS.config.database
MENU = KeyboardMenu()


def check_error(message):
    """ Принимает на вход сообщеник и проверяет, является ли оно командой бота
        Нужно для того, чтобы внутри потока можно было отлавливать команды
        Запускает команду, открывает главное меню или сообщает об ошибке
    """
    commands = {'/start': start_message,
                '/help': help_message,
                '/buses': buses_message,
                '/slavyanki': slavyanki_message,
                '/suburbans': suburbans_message,
                '/file': file_message,
                '/menu': menu_message}
    if message.text in commands:
        commands[message.text](message)
    elif message.text == 'Главное меню':
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, '', reply_markup=keyboard)
    else:
        keyboard = MENU.main_menu()
        error_msg = f'Произошла ошибка. ' \
                    f'Пользуйся стандартными кнопками или командами! /help'
        BOT.send_message(message.chat.id, error_msg, reply_markup=keyboard)


@BOT.message_handler(commands=['start'])
def start_message(message):
    """ Отправляет стартовое сообщение
    """
    answer = ANSWERS.start_answer()
    keyboard = MENU.main_menu()
    BOT.send_message(message.chat.id, answer,
                     reply_markup=keyboard, parse_mode='Markdown')
    DATABASE.add_user_data('start', message.chat.id)


@BOT.message_handler(commands=['help'])
def help_message(message):
    """ Отправляет сообщение с инструкцией
    """
    answer = ANSWERS.help_answer()
    keyboard = MENU.main_menu()
    BOT.send_message(message.chat.id, answer,
                     reply_markup=keyboard, parse_mode='Markdown')
    DATABASE.add_user_data('help', message.chat.id)


@BOT.message_handler(commands=['menu'])
def menu_message(message):
    """ Отправляет клавиатуру с главным меню
    """
    keyboard = MENU.main_menu()
    BOT.send_message(message.chat.id, '',
                     reply_markup=keyboard, parse_mode='Markdown')


@BOT.message_handler(commands=['buses'])
def buses_message(message):
    """ Отправляет клавиатуру с выбором направления для автобусов
    """
    keyboard = MENU.buses_message_menu()
    BOT.send_message(message.chat.id, 'Выбери направление',
                     reply_markup=keyboard)
    BOT.register_next_step_handler(message, buses_message_main)
    DATABASE.add_user_data('buses', message.chat.id)


def buses_message_main(message):
    """ Отправляет сообщение с автобусами на ближайший час и спрашивает
        о пересадках
    """
    possible_answers = {'Дубки ---> Одинцово': 'Дубки-Одинцово',
                        'Одинцово ---> Дубки': 'Одинцово-Дубки'}
    if message.text in possible_answers:
        direction = possible_answers[message.text]
        answer, buses = ANSWERS.buses_answer(direction)
        if len(buses) > 0:
            keyboard = MENU.pre_suburbans_after_buses_message_menu()
        else:
            keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
        BOT.register_next_step_handler(message, suburbans_after_buses_message,
                                       buses=buses, buses_direction=direction)
    else:
        check_error(message)


def suburbans_after_buses_message(message, buses, buses_direction):
    """ Отправляем клавиатуру с выбором направления электричек для поиска
        пересадок
    """
    if message.text == 'Посмотреть пересадки на электрички':
        keyboard = MENU.suburbans_after_buses_message_menu(buses_direction)
        BOT.send_message(message.chat.id, 'Выбери направление',
                         reply_markup=keyboard)
        BOT.register_next_step_handler(message,
                                       suburbans_after_buses_message_main,
                                       buses=buses,
                                       buses_direction=buses_direction)
    else:
        check_error(message)


def suburbans_after_buses_message_main(message, buses, buses_direction):
    """ Отправляет список удобных пересадок с автобусов на электрички и
        спрашивает, нужно ли показать все электрички по этому же направлению
    """
    if buses_direction == 'Дубки-Одинцово':
        possible_answers = {'Одинцово ---> Кунцево': 'Одинцово-Кунцево',
                            'Одинцово ---> Фили': 'Одинцово-Фили',
                            'Одинцово ---> Беговая': 'Одинцово-Беговая',
                            'Одинцово ---> Белорусский вокзал':
                                'Одинцово-Белорусский вокзал'}
    elif buses_direction == 'Одинцово-Дубки':
        possible_answers = {'Кунцево ---> Одинцово': 'Кунцево-Одинцово',
                            'Фили ---> Одинцово': 'Фили-Одинцово',
                            'Беговая ---> Одинцово': 'Беговая-Одинцово',
                            'Белорусский вокзал ---> Одинцово':
                                'Белорусский вокзал-Одинцово'}
    if message.text in possible_answers:
        suburbans_direction = possible_answers[message.text]
        answer = ANSWERS.suburbans_after_buses_answer(buses,
                                                      suburbans_direction)
        keyboard = MENU.after_suburbans_after_buses_message_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
        BOT.register_next_step_handler(message,
                                       suburbans_after_buses_message_last,
                                       suburbans_direction=suburbans_direction)
    else:
        check_error(message)


def suburbans_after_buses_message_last(message, suburbans_direction):
    """ Отправляет список электричек по выбранному ранее направлению и
        клавиатуру с главным меню
    """
    if message.text == 'Посмотреть все электрички':
        answer, suburbans = ANSWERS.suburbans_answer(suburbans_direction)
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
    else:
        check_error(message)


@BOT.message_handler(commands=['slavyanki'])
def slavyanki_message(message):
    """ Отправляет клавиатуру с выбором направления для славянок
    """
    keyboard = MENU.slavyanki_message_menu()
    BOT.send_message(message.chat.id, 'Выбери направление',
                     reply_markup=keyboard)
    BOT.register_next_step_handler(message, slavyanki_message_main)
    DATABASE.add_user_data('slavyanki', message.chat.id)


def slavyanki_message_main(message):
    """ Отправляет список славянок на сегодня
    """
    possible_answers = {'Дубки ---> Славянский бульвар': 'Дубки-Одинцово',
                        'Славянский бульвар ---> Дубки': 'Одинцово-Дубки'}
    if message.text in possible_answers:
        direction = possible_answers[message.text]
        answer = ANSWERS.slavyanki_answer(direction)
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
    else:
        check_error(message)


@BOT.message_handler(commands=['suburbans', 'trains'])
def suburbans_message(message):
    """ Отправляет клавиатуру с выбором направления для электричек
    """
    keyboard = MENU.suburbans_message_menu()
    BOT.send_message(message.chat.id, 'Выбери направление',
                     reply_markup=keyboard)
    BOT.register_next_step_handler(message, suburbans_message_main)
    DATABASE.add_user_data('trains', message.chat.id)


def suburbans_message_main(message):
    """ Отправляет сообщение с электричками на ближайший час и спрашивает
        о пересадках
    """
    possible_answers = {'Одинцово ---> Кунцево': 'Одинцово-Кунцево',
                        'Одинцово ---> Фили': 'Одинцово-Фили',
                        'Одинцово ---> Беговая': 'Одинцово-Беговая',
                        'Одинцово ---> Белорусский вокзал':
                            'Одинцово-Белорусский вокзал',
                        'Кунцево ---> Одинцово': 'Кунцево-Одинцово',
                        'Фили ---> Одинцово': 'Фили-Одинцово',
                        'Беговая ---> Одинцово': 'Беговая-Одинцово',
                        'Белорусский вокзал ---> Одинцово':
                            'Белорусский вокзал-Одинцово'}
    if message.text in possible_answers:
        suburbans_direction = possible_answers[message.text]
        answer, suburbans = ANSWERS.suburbans_answer(suburbans_direction)
        if len(suburbans) > 0:
            keyboard = MENU.pre_buses_after_suburbans_message_menu()
        else:
            keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
        BOT.register_next_step_handler(message, buses_after_suburbans_message,
                                       suburbans=suburbans)
    else:
        check_error(message)


def buses_after_suburbans_message(message, suburbans):
    """ Отправляет список автобусов с удобными пересадками на электрички и
        спрашивает, нужно ли показать все автобусы по этому же направлению
    """
    if message.text == 'Посмотреть пересадки на автобусы':
        buses_direction = ANSWERS.define_buses_direction_by_suburbans(
            suburbans)
        answer = ANSWERS.buses_after_suburbans_answer(suburbans)
        keyboard = MENU.after_buses_after_suburbans_message_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
        BOT.register_next_step_handler(message,
                                       buses_after_suburbans_message_last,
                                       buses_direction=buses_direction)
    else:
        check_error(message)


def buses_after_suburbans_message_last(message, buses_direction):
    """ Отправляет список автобусов по выбранному ранее направлению и
        клавиатуру с главным меню
    """
    if message.text == 'Посмотреть все автобусы':
        answer, suburbans = ANSWERS.buses_answer(buses_direction)
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
    else:
        check_error(message)


@BOT.message_handler(commands=['file'])
def file_message(message):
    """ Отправляет pdf-файл с расписание
    """
    filename = ANSWERS.config.buses_curriculum.filename
    doc = open(filename, 'rb')
    BOT.send_document(message.chat.id, doc)
    DATABASE.add_user_data('file', message.chat.id)


@BOT.message_handler(commands=['check_updates'])
def check_updates(message):
    """ Отравляет сообщение, доступное только для админа, с информацией о
        времени последнего обновления расписания
    """
    if message.from_user.id == ADMIN_ID:
        answer = ANSWERS.check_updates()
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, answer,
                         reply_markup=keyboard, parse_mode='Markdown')
    else:
        error_msg = 'Недостаточно прав для вызова этой команды.'
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, error_msg, reply_markup=keyboard)


@BOT.message_handler(commands=['statistics'])
def get_statistics(message):
    """ Сохраняет статистику из базы данных в xlsx-файл и отправляет его
    """
    DATABASE.get_statistics_in_xcl()
    doc = open('statistics.xlsx', 'rb')
    if message.from_user.id == ADMIN_ID:
        BOT.send_document(message.chat.id, doc)
    else:
        error_msg = 'Недостаточно прав для вызова этой команды.'
        keyboard = MENU.main_menu()
        BOT.send_message(message.chat.id, error_msg, reply_markup=keyboard)


@BOT.message_handler(content_types=['text',
                                    'audio', 'sticker', 'video', 'document'])
def other_messages(message):
    """ Обработчик для всех остальных сообщений, на которые бот не умеет
        отвечать
    """
    error_msg = 'Я не умею отвечать на такие сообщения :('
    keyboard = MENU.main_menu()
    BOT.send_message(message.chat.id, error_msg, reply_markup=keyboard)


BOT.polling(none_stop=True)
