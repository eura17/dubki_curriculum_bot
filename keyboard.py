# -*- coding: utf-8 -*-

from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class KeyboardMenu:
    def __init__(self):
        self.keyboard = ReplyKeyboardMarkup(True, True)

    def reset_keyboard(self):
        self.keyboard = ReplyKeyboardMarkup(True, True)

    def main_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Автобусы'))
        self.keyboard.add(KeyboardButton('Славянки'))
        self.keyboard.add(KeyboardButton('Электрички'))
        self.keyboard.add(KeyboardButton('Файл'))
        return self.keyboard

    def buses_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Дубки ---> Одинцово'),
                          KeyboardButton('Одинцово ---> Дубки'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def pre_suburbans_after_buses_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Посмотреть пересадки на электрички'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def suburbans_after_buses_message_menu(self, buses_direction: str):
        self.reset_keyboard()
        if buses_direction == 'Дубки-Одинцово':
            self.keyboard.add(KeyboardButton('Одинцово ---> Кунцево'),
                              KeyboardButton('Одинцово ---> Фили'))
            self.keyboard.add(KeyboardButton('Одинцово ---> Беговая'),
                              KeyboardButton(
                                  'Одинцово ---> Белорусский вокзал'))
        elif buses_direction == 'Одинцово-Дубки':
            self.keyboard.add(KeyboardButton(
                'Белорусский вокзал ---> Одинцово'),
                              KeyboardButton('Беговая ---> Одинцово'))
            self.keyboard.add(KeyboardButton('Фили ---> Одинцово'),
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
                          KeyboardButton('Одинцово ---> Фили'))
        self.keyboard.add(KeyboardButton('Одинцово ---> Беговая'),
                          KeyboardButton('Одинцово ---> Белорусский вокзал'))
        self.keyboard.add(KeyboardButton('Белорусский вокзал ---> Одинцово'),
                          KeyboardButton('Беговая ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Фили ---> Одинцово'),
                          KeyboardButton('Кунцево ---> Одинцово'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def pre_buses_after_suburbans_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Посмотреть пересадки на автобусы'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard

    def after_buses_after_suburbans_message_menu(self):
        self.reset_keyboard()
        self.keyboard.add(KeyboardButton('Посмотреть все автобусы'))
        self.keyboard.add(KeyboardButton('Главное меню'))
        return self.keyboard
