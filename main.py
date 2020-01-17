# -*- coding: utf-8 -*-

import fitz
import pandas as pd
from urllib.request import urlretrieve as download, urlopen as opener
from threading import Thread, Lock
from bs4 import BeautifulSoup
from time import sleep
import requests
import datetime
import os
import shutil
import openpyxl as xl
import psycopg2 as sql


class Answers:
    def __init__(self):
        pass

    @staticmethod
    def startMessage():
        message = '''Привет, дубчанин!
Я бот, с помощью которого ты сможешь узнать расписание ближайших автобусов.
Да, тебе не придется лезть в группу в ВК, я сделаю это за тебя.
Инструкция по работе /help
P.S. По всем вопросам и предложениям писать @eura71'''
        return message

    @staticmethod
    def helpMessage():
        message = '''Вот весь список команд, с помощью которых ты можешь управлять мной:
/buses - список автобусов на ближайший час
/slavyanki - список славянок на сегодня
/trains - список электричек на ближайший час
/file - PDF-файл с расписанием'''
        return message

    @staticmethod
    def busesMessage(direction):
        buses, time = Setup.timeAndWeekday()
        hours, minutes = time[0], time[1]

        relevantBuses = []

        for bus in buses[direction]:
            if isinstance(bus, tuple):
                hoursDep = bus[0][0]
                minutesDep = bus[0][1]
                if (hoursDep == hours and minutesDep >= minutes) or \
                        (hoursDep == hours + 1 and minutesDep <= minutes):
                    answer = bus[2]
                    departureTime = bus[0]

                    delta = abs((time[0] * 60 + time[1]) - (departureTime[0] * 60 + departureTime[1]))
                    textDelta = ' (через {})'
                    if 11 <= delta <= 19:
                        addDelta = textDelta.format('{} минут'.format(delta))
                    elif delta % 10 == 1:
                        addDelta = textDelta.format('{} минуту'.format(delta))
                    elif delta % 10 in [2, 3, 4]:
                        addDelta = textDelta.format('{} минуты'.format(delta))
                    elif delta % 10 in [5, 6, 7, 8, 9, 0]:
                        addDelta = textDelta.format('{} минут'.format(delta))
                    answer += addDelta

                    relevantBuses.append(answer)

        if len(relevantBuses) == 0:
            message = 'К сожалению, в ближайший час нет автобусов :('
        else:
            message = 'Список автобусов на ближайший час:\n'
            for bus in relevantBuses:
                message += '\n' + bus
            trains = '\n\n' + r'Ближайшие электрички /trains'
            message += trains

        return message


    @staticmethod
    def slavyankiMessage(direction):
        gram = {'Дубки-Одинцово': 'от Дубков до Славянского бульвара',
                'Одинцово-Дубки': 'от Славянского бульвара до Дубков'}
        buses, time = Setup.timeAndWeekday()
        hours, minutes = time[0], time[1]
        relevantBuses = []
        for bus in buses[direction]:
            if isinstance(bus, tuple):
                if 'славянка' in bus[2] and ((hours == bus[0][0] and minutes <= bus[0][1]) or \
                        (hours < bus[0][0])):
                    answer = bus[2][:bus[2].find('(')]
                    departureTime = bus[0]

                    delta = abs((time[0] * 60 + time[1]) - (departureTime[0] * 60 + departureTime[1]))
                    textDelta = ' (через {})'
                    if 11 <= delta <= 19:
                        addDelta = textDelta.format('{} минут'.format(delta))
                    elif delta % 10 == 1:
                        addDelta = textDelta.format('{} минуту'.format(delta))
                    elif delta % 10 in [2, 3, 4]:
                        addDelta = textDelta.format('{} минуты'.format(delta))
                    elif delta % 10 in [5, 6, 7, 8, 9, 0]:
                        addDelta = textDelta.format('{} минут'.format(delta))
                    if delta < 60:
                        answer += addDelta

                    relevantBuses.append(answer)

        if len(relevantBuses) == 0:
            message = 'К сожалению, славянок сегодня больше нет :('
            message += '\n\nБлижайшие автобусы /buses'
        else:
            message = 'Список славянок на сегодня {}:\n'.format(gram[direction])
            for line in relevantBuses:
                message += '\n' + line

        return message

    @staticmethod
    def trainsMessage(direction):
        startStation, endStation = direction.split('-')
        hours, minutes = Setup.timeAndWeekday(forYandex=True)[1]
        relevant = []
        answer = '''
*{} ({})*: 
отправление ({}) в *{}*
прибытие ({}) в *{}*'''

        for train in suburbanCurriculum[direction]:
            if isinstance(train, tuple):
                hoursDep, minutesDep = train[0][0], train[0][1]
                if (hours == hoursDep and minutes <= minutesDep) or \
                        (hours + 1 == hoursDep and minutes >= minutesDep):
                    suburbanName = train[2]['name']
                    suburbanType = train[2]['type']
                    departureTime = train[2]['departure']
                    arrivalTime = train[2]['arrival']
                    relevant.append(answer.format(suburbanName, suburbanType,
                                                  startStation, departureTime,
                                                  endStation, arrivalTime))

        if len(relevant) == 0:
            message = 'К сожалению, в ближайший час нет электричек :('
        else:
            message = 'Список электричек на ближайший час:'
            for line in relevant:
                message += ('\n' + line)
            message += '\n\nБлижайшие автобусы /buses'

        return message


class Setup:
    def __init__(self):
        pass

    @staticmethod
    def creatorBusesCurriculum():
        global weekCurriculum, satCurriculum, sunCurriculum

        dubki = 'https://vk.com/dubki'
        groupPage = BeautifulSoup(opener(dubki), features='html.parser')
        for a in groupPage.find_all('a', href=True):
            if 'Расписание' in str(a):
                linkToDoc = a['href']
                download(linkToDoc, filename='Расписание.pdf')
                break

        path = os.getcwd() + '/txt'
        os.mkdir(path)

        pdf_document = 'Расписание.pdf'
        doc = fitz.open(pdf_document)
        page1 = doc.loadPage(0)
        text1 = page1.getText('text')
        page2 = doc.loadPage(1)
        text2 = page2.getText('text')
        with open('txt/mon-fri.txt', 'w', encoding='utf8') as f:
            print(text1, file=f)
        with open('txt/sat-sun.txt', 'w', encoding='utf8') as f:
            print(text2, file=f)

        p, k, s, c, = 0, 0, 0, -1
        weekOrSatOrSun = 'week'
        DtoOweekTimes, OtoDweekTimes = [], []
        DtoOsatTimes, OtoDsatTimes = [], []
        DtoOsunTimes, OtoDsunTimes = [], []
        sixSubMem = [0, 0, 0]
        for rasp in range(2):
            if rasp == 0:
                days = 'mon-fri'
            elif rasp == 1:
                days = 'sat-sun'
                weekOrSatOrSun = 'sat'
                s, k = 0, 0
            with open('txt/{}.txt'.format(days), 'r', encoding='utf8') as f:
                for elem in f:

                    predict = False
                    slavyanka = False
                    elem = elem.strip()

                    if elem == '----':
                        res = [404, 404]

                    elif elem == 'по прибыт.':
                        predict = True
                        hours, minutes = int(dubki[0]), int(dubki[1])
                        if minutes + 15 >= 60:
                            hours += 1
                            minutes -= 45
                        elif minutes + 15 < 60:
                            minutes += 15
                        res = [hours, minutes]

                    else:
                        try:
                            if elem[-2:] == '**':
                                slavyanka = True
                                elem = elem[:-2]
                            elif elem[-1] == '*':
                                slavyanka = True
                                elem = elem[:-1]
                            elem = list(map(int, elem.split(':')))
                            hours, minutes = int(elem[0]), int(elem[1])
                            res = [hours, minutes]
                        except Exception:
                            continue

                    if res[0] in [0, 1, 2, 3, 4, 5]:
                        res[0] += 24

                    s += 1
                    if s in [1, 3, 5] and k == 0 and weekOrSatOrSun != 'week':
                        c += 1
                        sixSubMem[c] = res[0]
                        if weekOrSatOrSun == 'sat' and s == 5:
                            try:
                                check = int(sixSubMem[0]) <= \
                                        int(sixSubMem[1]) <= \
                                        int(sixSubMem[2])
                                if check:
                                    c = -1
                                    s = -1
                                    sixSubMem = [0, 0, 0]
                                elif s == 5:
                                    weekOrSatOrSun = 'sun'
                            except Exception:
                                c = -1
                                s = -1
                                sixSubMem = [0, 0, 0]

                    if k == 0:
                        dubki = res
                        if weekOrSatOrSun == 'week':
                            DtoOweekTimes.append((res, predict, slavyanka))
                        elif weekOrSatOrSun == 'sat':
                            DtoOsatTimes.append((res, predict, slavyanka))
                        elif weekOrSatOrSun == 'sun':
                            DtoOsunTimes.append((res, predict, slavyanka))
                        k += 1
                    elif k == 1:
                        if weekOrSatOrSun == 'week':
                            OtoDweekTimes.append((res, predict, slavyanka))
                        elif weekOrSatOrSun == 'sat':
                            OtoDsatTimes.append((res, predict, slavyanka))
                        elif weekOrSatOrSun == 'sun':
                            OtoDsunTimes.append((res, predict, slavyanka))
                        k = 0

        weekCurriculum = Setup.dictToDf(DtoOweekTimes, OtoDweekTimes)

        satCurriculum = Setup.dictToDf(DtoOsatTimes, OtoDsatTimes)

        sunCurriculum = Setup.dictToDf(DtoOsunTimes, OtoDsunTimes)

        shutil.rmtree(path)


    @staticmethod
    def dictToDf(timesDubki, timesOdintsovo):
        times = {'Дубки-Одинцово': [], 'Одинцово-Дубки': []}

        timesDubki.sort()
        timesOdintsovo.sort()

        for elem in timesDubki:
            DtoO = ''
            if elem[0][0] == 404 and elem[0][1] == 404:
                continue
            if isinstance(elem[0][0], int) and isinstance(elem[0][1], int):
                hours, minutes = elem[0][0], elem[0][1]
                if hours in [24, 25, 26, 27, 28, 29]:
                    hours -= 24
                if minutes + 15 >= 60:
                    hAr = hours + 1
                    mAr = minutes - 45
                elif minutes + 15 < 60:
                    hAr = hours
                    mAr = minutes + 15

                hours, minutes = str(hours), str(minutes)
                if len(hours) == 1:
                    hours = '0' + hours
                if len(minutes) == 1:
                    minutes = '0' + minutes
                DtoO = hours + ':' + minutes
            if elem[1]:
                DtoO = 'по прибытии ~ *{}*'.format(DtoO)
            elif not elem[1]:
                DtoO = 'по расписанию *{}*'.format(DtoO)
            if elem[2]:
                DtoO += ' (*славянка*)'
            times['Дубки-Одинцово'].append(([elem[0][0], elem[0][1]], [hAr, mAr], DtoO))

        for elem in timesOdintsovo:
            OtoD = ''
            if isinstance(elem[0][0], int) and isinstance(elem[0][1], int):
                hours, minutes = elem[0][0], elem[0][1]
                if hours in [24, 25, 26, 27, 28, 29]:
                    hours -= 24
                if minutes + 15 >= 60:
                    hAr = hours + 1
                    mAr = minutes - 45
                elif minutes + 15 < 60:
                    hAr = hours
                    mAr = minutes + 15

                hours, minutes = str(hours), str(minutes)
                if len(hours) == 1:
                    hours = '0' + hours
                if len(minutes) == 1:
                    minutes = '0' + minutes
                OtoD = hours + ':' + minutes
            if elem[1]:
                OtoD = 'по прибытии ~ *{}*'.format(OtoD)
            elif not elem[1]:
                OtoD = 'по расписанию *{}*'.format(OtoD)
            if elem[2]:
                OtoD += ' (*славянка*)'
            times['Одинцово-Дубки'].append(([elem[0][0], elem[0][1]], [hAr, mAr], OtoD))

        df1 = pd.DataFrame({'Дубки-Одинцово': times['Дубки-Одинцово']})
        df2 = pd.DataFrame({'Одинцово-Дубки': times['Одинцово-Дубки']})
        cur = pd.concat([df1, df2], axis=1)
        return cur


    @staticmethod
    def creatorTrainsCurriculum():
        global suburbanCurriculum

        stations = {'Одинцово': 'c10743',
                    'Кунцево': 's9601728',
                    'Фили': 's9600821',
                    'Беговая': 's9601666',
                    'Белорусский вокзал': 's2000006'}
        suburbanTypes = {'stdplus': 'Стандарт плюс',
                         'suburban': 'Обычная электричка',
                         'rex': 'Экспресс РЭКС',
                         'mcd1': 'Иволга',
                         'aerstd': 'Аэроэкспресс'}

        apikey = '7cf62f2f-49ce-4194-afae-fe86b8001542'
        url = 'https://api.rasp.yandex.net/v3.0/search/?apikey={}&from={}&to={}&date={}'
        default = '&format=json&limit=1000&lang=ru_RU&system=yandex&show_systems=yandex'
        date, time = Setup.timeAndWeekday(forYandex=True)
        nowHours, nowMinutes = time[0], time[1]
        timetable = {'Одинцово-Кунцево': [], 'Кунцево-Одинцово': [],
                     'Одинцово-Фили': [], 'Фили-Одинцово': [],
                     'Одинцово-Беговая': [], 'Беговая-Одинцово': [],
                     'Одинцово-Белорусский вокзал': [], 'Белорусский вокзал-Одинцово': []}

        for day in range(2):
            if nowHours + 3 < 24 and day == 1:
                break
            if day == 1:
                try:
                    date = datetime.datetime(
                        year=datetime.datetime.today().date().year,
                        month=datetime.datetime.today().date().month,
                        day=datetime.datetime.today().date().day + 1)
                except Exception:
                    try:
                        date = datetime.datetime(
                            year=datetime.datetime.today().date().year,
                            month=datetime.datetime.today().date().month + 1,
                            day=1)
                    except Exception:
                        date = datetime.datetime(
                            year=datetime.datetime.today().date().year + 1,
                            month=1,
                            day=1)

            for stat in ['Кунцево', 'Фили', 'Беговая', 'Белорусский вокзал']:
                request = requests.get(url.format(apikey,
                                                  stations['Одинцово'],
                                                  stations[stat],
                                                  date) + default).json()
                if 'error' in request:
                    break
                else:
                    trains = request['segments']
                    for train in trains:

                        departureTime = train['departure'][train['departure'].find('T') + 1:train['departure'].find('T') + 6]
                        arrivalTime = train['arrival'][train['arrival'].find('T') + 1:train['arrival'].find('T') + 6]
                        suburbanName = train['thread']['title']
                        suburbanType = suburbanTypes[train['thread']['transport_subtype']['code']]

                        info = {'departure': departureTime,
                                'arrival': arrivalTime,
                                'name': suburbanName,
                                'type': suburbanType}

                        dep = list(map(int, departureTime.split(':')))
                        if dep[0] in {0, 1, 2}:
                            dep[0] += 24
                        arr = list(map(int, arrivalTime.split(':')))
                        if arr[0] in {0, 1, 2}:
                            arr[0] += 24

                        fullInfo = (dep, arr, info)
                        if (nowHours - 3 <= dep[0] <= nowHours + 3) or (nowHours - 3 <= arr[0] <= nowHours + 3):
                            timetable['Одинцово-{}'.format(stat)].append(fullInfo)

                request = requests.get(url.format(apikey,
                                                  stations[stat],
                                                  stations['Одинцово'],
                                                  date) + default).json()
                if 'error' in request:
                    break
                else:
                    trains = request['segments']
                    for train in trains:

                        departureTime = train['departure'][train['departure'].find('T') + 1:train['departure'].find('T') + 6]
                        arrivalTime = train['arrival'][train['arrival'].find('T') + 1:train['arrival'].find('T') + 6]
                        suburbanName = train['thread']['title']
                        suburbanType = suburbanTypes[train['thread']['transport_subtype']['code']]

                        info = {'departure': departureTime,
                                'arrival': arrivalTime,
                                'name': suburbanName,
                                'type': suburbanType}

                        dep = list(map(int, departureTime.split(':')))
                        if dep[0] in {0, 1, 2}:
                            dep[0] += 24
                        arr = list(map(int, arrivalTime.split(':')))
                        if arr[0] in {0, 1, 2}:
                            arr[0] += 24

                        fullInfo = (dep, arr, info)
                        if (nowHours - 3 <= dep[0] <= nowHours + 3) or (nowHours - 3 <= arr[0] <= nowHours + 3):
                            timetable['{}-Одинцово'.format(stat)].append(fullInfo)

        df1 = pd.DataFrame({'Одинцово-Кунцево': timetable['Одинцово-Кунцево']})
        df2 = pd.DataFrame({'Одинцово-Фили': timetable['Одинцово-Фили']})
        df3 = pd.DataFrame({'Одинцово-Беговая': timetable['Одинцово-Беговая']})
        df4 = pd.DataFrame({'Одинцово-Белорусский вокзал': timetable['Одинцово-Белорусский вокзал']})
        df5 = pd.DataFrame({'Белорусский вокзал-Одинцово': timetable['Белорусский вокзал-Одинцово']})
        df6 = pd.DataFrame({'Беговая-Одинцово': timetable['Беговая-Одинцово']})
        df7 = pd.DataFrame({'Фили-Одинцово': timetable['Фили-Одинцово']})
        df8 = pd.DataFrame({'Кунцево-Одинцово': timetable['Кунцево-Одинцово']})

        suburbanCurriculum = pd.concat([df1, df2, df3, df4, df5, df6, df7, df8], axis=1)


    @staticmethod
    def timeAndWeekday(forYandex=False):
        today = datetime.datetime.today()
        time = [today.time().hour, today.time().minute]
        time[0] = (time[0] + 3) % 24
        if time[0] in {0, 1, 2}:
            time[0] += 24

        if not forYandex:
            numToDay = {1: weekCurriculum,
                        2: weekCurriculum,
                        3: weekCurriculum,
                        4: weekCurriculum,
                        5: weekCurriculum,
                        6: satCurriculum,
                        7: sunCurriculum}

            numWeek = today.isoweekday()
            if numWeek == 1 and time[0] in {24, 25, 26}:
                numWeek = 7
            elif numWeek == 6 and time[0] in {24, 25, 27}:
                numWeek = 5
            elif numWeek == 7 and time[0] in {24, 25, 27}:
                numWeek = 6
            weekday = numToDay[numWeek]
            return weekday, time
        else:
            date = today.date()
            return date, time

    @staticmethod
    def createDataBase():
        con = sql.connect(os.getenv('DATABASE_URL'),
                          sslmode='require')
        cur = con.cursor()
        # создание таблицы full_statistics
        cur.execute('''CREATE TABLE FULL_STATISTICS
                    (date TEXT PRIMARY KEY,
                    start_calls INT,
                    help_calls INT,
                    buses_calls INT,
                    slavyanki_calls INT,
                    trains_calls INT,
                    file_calls INT,
                    total_calls INT);''')
        # создание таблицы users_statistics
        cur.execute('''CREATE TABLE USERS_STATISTICS
                    (id INT PRIMARY KEY NOT NULL,
                    start_date TEXT,
                    lastcall_date TEXT,
                    total_calls INT);''')
        con.commit()
        con.close()

    @staticmethod
    def setup():
        global lastUpdateTrains, lastUpdateBuses

        start = datetime.datetime.now()
        print('Первоначальная настройка началась...')
        Setup.creatorBusesCurriculum()
        print('Расписание автобусов загружено...')
        lastUpdateBuses = datetime.datetime.now() + datetime.timedelta(hours=3)
        Setup.creatorTrainsCurriculum()
        print('Расписание электричек загружено...')

        if bool(int((os.getenv('CREATE_DB')))):
            Setup.createDataBase()
            print('База данных создана.')

        end = datetime.datetime.now()
        print('Настройка прошла успешно ({}). Бот готов к работе.'.format(end-start))
        lastUpdateTrains = end + datetime.timedelta(hours=3)

        def updateTrainsCurriculum():
            global lastUpdateTrains

            with Lock():
                while True:
                    sleep(3600)
                    start = datetime.datetime.now()
                    Setup.creatorTrainsCurriculum()
                    end = datetime.datetime.now()
                    print('Расписание электричек было обновлено за {}'.format(end-start))
                    lastUpdateTrains = end + datetime.timedelta(hours=3)

        def updateBusesCurriculum():
            global lastUpdateBuses

            with Lock():
                while True:
                    sleep(3600 * 12)
                    start = datetime.datetime.now()
                    Setup.creatorBusesCurriculum()
                    end = datetime.datetime.now()
                    print('Расписание автобусов было обновлено за {}'.format(end - start))
                    lastUpdateBuses = end + datetime.timedelta(hours=3)

        updateTrainsThread = Thread(target=updateTrainsCurriculum, name='updateTrainsCurricullum', daemon=True)
        updateBusesThread = Thread(target=updateBusesCurriculum, name='updateBusesCurriculum', daemon=True)
        updateTrainsThread.start()
        updateBusesThread.start()


class Admin:
    def __init__(self):
        pass

    @staticmethod
    def checkUpdates():
        answer = '''Последнее обновление расписания электричек: *{}*
Последнее обновление расписания автобусов: *{}*'''.format(lastUpdateTrains, lastUpdateBuses)
        return answer

    @staticmethod
    def userData(userID: int, func: str):
        today = datetime.datetime.now().date()
        con = sql.connect(os.getenv('DATABASE_URL'),
                          sslmode='require')
        cur = con.cursor()

        # работа с таблицей full_statistics
        funcs = {'start': 1,
                 'buses': 2,
                 'slavyanki': 3,
                 'trains': 4,
                 'file': 5,
                 'total': 6}
        cur.execute('SELECT * from FULL_STATISTICS WHERE date LIKE \'{}\';'.format(today))
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.execute('INSERT INTO FULL_STATISTICS (date, start_calls, buses_calls, slavyanki_calls, trains_calls, file_calls, total_calls) VALUES (\'{}\', {}, {}, {}, {}, {}, {});'.format(
                today, 0, 0, 0, 0, 0, 0))
            con.commit()
        cur.execute('UPDATE FULL_STATISTICS set {}_calls = {} where date LIKE \'{}\';'.format(
            func, int(rows[0][funcs[func]]) + 1, today))
        cur.execute('UPDATE FULL_STATISTICS set total_calls = {} where date LIKE \'{}\';'.format(
            rows[0][funcs['total']] + 1, today))
        con.commit()

        # работа с таблицей users_statistics
        cur.execute('SELECT * from USERS_STATISTICS WHERE id = {}'.format(userID))
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.execute('INSERT INTO USERS_STATISTICS (id, start_date, total_calls) VALUES ({}, {}, {});'.format(
                userID, today, 0))
        cur.execute('UPDATE USERS_STATISTICS set lastcall_date = {} WHERE id = {};'.format(
            today, userID))
        cur.execute('UPDATE USERS_STATISTICS set total_calls = {} WHERE id = {};'.format(
            int(rows[0][3]) + 1, userID))
        con.commit()

        con.close()


Setup.setup()
