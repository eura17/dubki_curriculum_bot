# -*- coding: utf-8 -*-

from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class KeyboardMenu:
    def __init__(self):
        self.keyboard = ReplyKeyboardMarkup(True)

    def reset_keyboard(self):
        self.keyboard = ReplyKeyboardMarkup(True)

    def main_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Автобусы'))
        self.keyboard.add(KeyboardButton('Славянки'))
        self.keyboard.add(KeyboardButton('Электрички'))
        self.keyboard.add(KeyboardButton('Файл с расписанием'))
        return self.keyboard

    def buses_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Дубки ---> Одинцово'),
                          KeyboardButton('Одинцово ---> Дубки'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def pre_suburbans_after_buses_message_menu(self, buses_direction: str):
        self.reset_keyboard()
        if buses_direction == 'Дубки-Одинцово':
            self.keyboard.add(KeyboardButton('Посмотреть пересадки на электрички'))
        elif buses_direction == 'Одинцово-Дубки':
            self.keyboard.add(KeyboardButton('Посмотреть пересадки с электричек'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def suburbans_after_buses_message_menu(self, buses_direction: str):
        self.reset_keyboard()
        if buses_direction == 'Дубки-Одинцово':
            self.keyboard.add(KeyboardButton('Одинцово ---> Кунцево'),
                              KeyboardButton('Одинцово ---> Славянский бульвар'),
                              KeyboardButton('Одинцово ---> Фили'))
            self.keyboard.add(KeyboardButton('Одинцово ---> Беговая'),
                              KeyboardButton(
                                  'Одинцово ---> Белорусский вокзал'))
        elif buses_direction == 'Одинцово-Дубки':
            self.keyboard.add(KeyboardButton(
                'Белорусский вокзал ---> Одинцово'),
                              KeyboardButton('Беговая ---> Одинцово'))
            self.keyboard.add(KeyboardButton('Фили ---> Одинцово'),
                              KeyboardButton('Славянский бульвар ---> Одинцово'),
                              KeyboardButton('Кунцево ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def after_suburbans_after_buses_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Посмотреть все электрички'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def slavyanki_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Дубки ---> Славянский бульвар'),
                          KeyboardButton('Славянский бульвар ---> Дубки'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def suburbans_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Одинцово ---> Кунцево'),
                          KeyboardButton('Кунцево ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Одинцово ---> Славянский бульвар'),
                          KeyboardButton('Славянский бульвар ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Одинцово ---> Фили'),
                          KeyboardButton('Фили ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Одинцово ---> Беговая'),
                          KeyboardButton('Беговая ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Одинцово ---> Белорусский вокзал'),
                          KeyboardButton('Белорусский вокзал ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def pre_buses_after_suburbans_message_menu(self, suburbans_direction: str):
        self.reset_keyboard()
        suburbans_direction_from = suburbans_direction.split('-')[0]
        if suburbans_direction_from == 'Одинцово':
            self.keyboard.add(KeyboardButton('Посмотреть пересадки с автобусов'))
        else:
            self.keyboard.add(KeyboardButton('Посмотреть пересадки на автобусы'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def after_buses_after_suburbans_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Посмотреть все автобусы'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard
