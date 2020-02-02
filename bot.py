# -*- coding: utf-8 -*-

import telebot
from telebot.types import KeyboardButton
import os
from config import Answers, Admin

TOKEN = os.getenv('TOKEN')
myID = 281452837
bot = telebot.TeleBot(TOKEN)
answers = Answers()
admin = Admin()


def exceptionHandlerForAnswers(func):
    def wrap(message):
        try:
            func(message)
        except Exception as e:
            bot.send_message(message.chat.id, 'Произошла какая-то ошибка :(')
            print(e)
    return wrap


@exceptionHandlerForAnswers
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, answers.startAnswer(), parse_mode='Markdown')
    admin.userData(message.chat.id, func='start')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, answers.helpAnswer(), parse_mode='Markdown')
    admin.userData(message.chat.id, func='help')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['buses'])
def buses_message(message):
    keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard1.row('Дубки ---> Одинцово', 'Одинцово ---> Дубки')
    bot.send_message(message.chat.id, 'Выбери направление', reply_markup=keyboard1)
    bot.register_next_step_handler(message, buses_message_main)
    admin.userData(message.chat.id, func='buses')


def buses_message_main(message):
    commandsBuses = {'Дубки ---> Одинцово': 'Дубки-Одинцово',
                     'Одинцово ---> Дубки': 'Одинцово-Дубки'}
    bot.send_message(message.chat.id,
                     answers.busesAnswer(direction=commandsBuses[message.text]),
                     parse_mode='Markdown')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['slavyanki'])
def slavyanki_message(message):
    keyboard2 = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard2.row('Дубки ---> Славянский бульвар', 'Славянский бульвар ---> Дубки')
    bot.send_message(message.chat.id, 'Выбери направление', reply_markup=keyboard2)
    bot.register_next_step_handler(message, slavyanki_message_main)
    admin.userData(message.chat.id, func='slavyanki')


def slavyanki_message_main(message):
    commands = {'Дубки ---> Славянский бульвар': 'Дубки-Одинцово',
                'Славянский бульвар ---> Дубки': 'Одинцово-Дубки'}
    bot.send_message(message.chat.id,
                     answers.slavyankiAnswer(commands[message.text]),
                     parse_mode='Markdown')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['trains'])
def trains_message(message):
    keyboard3 = telebot.types.ReplyKeyboardMarkup(True, True)
    keyboard3.add(KeyboardButton('Одинцово ---> Кунцево'),
                  KeyboardButton('Одинцово ---> Фили'))
    keyboard3.add(KeyboardButton('Одинцово ---> Беговая'),
                  KeyboardButton('Одинцово ---> Белорусский вокзал'))
    keyboard3.add(KeyboardButton('Белорусский вокзал ---> Одинцово'),
                  KeyboardButton('Беговая ---> Одинцово'))
    keyboard3.add(KeyboardButton('Фили ---> Одинцово'),
                  KeyboardButton('Кунцево ---> Одинцово'))
    bot.send_message(message.chat.id, 'Выбери направление', reply_markup=keyboard3)
    bot.register_next_step_handler(message, trains_message_main)
    admin.userData(message.chat.id, func='trains')


def trains_message_main(message):
    commandsTrains = {'Одинцово ---> Кунцево': 'Одинцово-Кунцево',
                      'Одинцово ---> Фили': 'Одинцово-Фили',
                      'Одинцово ---> Беговая': 'Одинцово-Беговая',
                      'Одинцово ---> Белорусский вокзал': 'Одинцово-Белорусский вокзал',
                      'Кунцево ---> Одинцово': 'Кунцево-Одинцово',
                      'Фили ---> Одинцово': 'Фили-Одинцово',
                      'Беговая ---> Одинцово': 'Беговая-Одинцово',
                      'Белорусский вокзал ---> Одинцово': 'Белорусский вокзал-Одинцово'}
    bot.send_message(message.chat.id,
                     answers.trainsMessage(commandsTrains[message.text]),
                     parse_mode='Markdown')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['file'])
def file_message(message):
    doc = open('Расписание.pdf', 'rb')
    bot.send_document(message.chat.id, doc)
    admin.userData(message.chat.id, func='file')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['check_updates'])
def check_updates(message):
    if message.from_user.id == myID:
        bot.send_message(message.chat.id, admin.checkUpdates(answers), parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, 'Недостаточно прав для вызова этой команды.')


@exceptionHandlerForAnswers
@bot.message_handler(commands=['get_statistics'])
def get_statistics(message):
    admin.createStatisticsXcl()
    doc = open('statistics.xlsx', 'rb')
    if message.from_user.id == myID:
        bot.send_document(message.chat.id, doc)
    else:
        bot.send_message(message.chat.id, 'Недостаточно прав для вызова этой команды.')


@bot.message_handler(content_types=['text', 'audio', 'sticker', 'video', 'document'])
def text_messages(message):
    bot.send_message(message.chat.id, 'Я пока не умею отвечать на такие сообщения :( /help')


bot.polling(none_stop=True)
