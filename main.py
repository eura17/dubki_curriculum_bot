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


class Answers:
    def __init__(self):
        pass

    @staticmethod
    def startMessage():
        message = '''Привет, дубчанин!
Я бот, с помощью которого ты сможешь узнать расписание ближайших автобусов.
Да, тебе не придется лезть в группу в ВК, я сделаю это за тебя.
Инструкция по работе со мной доступна по команде /help
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
        startPoint = direction.split('-')[0]

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
        apikey = '7cf62f2f-49ce-4194-afae-fe86b8001542'
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
    def createWorkbook():
        if 'statistics.xlsx' not in os.listdir(os.getcwd()):
            wb = xl.workbook.Workbook()
            wb.active.title = 'full_statistics'
            wb.create_sheet('users_statistics', 1)

            fullStat = wb['full_statistics']
            names1 = {'A1': 'data',
                      'B1': 'new_users',
                      'C1': 'buses_calls',
                      'D1': 'slavyanki_calls',
                      'E1': 'trains_calls',
                      'F1': 'file_calls',
                      'G1': 'total_calls'}
            for elem in names1:
                fullStat[elem] = names1[elem]

            usersStat = wb['users_statistics']
            names2 = {'A1': 'id',
                      'B1': 'start_data',
                      'C1': 'last_call_data',
                      'D1': 'buses_calls',
                      'E1': 'slavyanki_calls',
                      'F1': 'trains_calls',
                      'G1': 'file_calls',
                      'H1': 'total_calls'}
            for elem in names2:
                usersStat[elem] = names2[elem]
            wb.save(filename='statistics.xlsx')


    @staticmethod
    def setup():
        global lastUpdateTrains, lastUpdateBuses

        start = datetime.datetime.now()
        Setup.creatorBusesCurriculum()
        lastUpdateBuses = datetime.datetime.now() + datetime.timedelta(hours=3)
        Setup.creatorTrainsCurriculum()
        Setup.createWorkbook()
        end = datetime.datetime.now()
        print('Первый запуск прошел успешно ({}). Бот готов к работе.'.format(end-start))
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
    def userData(userID, func='start'):
        funcs = {'start': 2,
                 'buses': 3,
                 'slavyanki': 4,
                 'trains': 5,
                 'file': 6,
                 'total': 7}

        wb = xl.load_workbook(filename='statistics.xlsx')  # statistics.xlsx

        # работа с full_statistics
        fullStatisticsSheet = wb['full_statistics']
        addDate = str(datetime.datetime.today().strftime('%d.%m.%Y'))
        # добавление новой даты, если еще не было
        isDateExists = False
        for i in range(1, fullStatisticsSheet.max_row + 1):
            if addDate == fullStatisticsSheet.cell(row=i, column=1).value:
                isDateExists = True
                currentRow = i
                break
        if not isDateExists:
            currentRow = fullStatisticsSheet.max_row + 1
            forTotal = '=SUM(C{}:F{})'.format(currentRow, currentRow)
            totalCell = fullStatisticsSheet.cell(row=currentRow, column=8)
            totalCell.value = forTotal
        fullStatisticsSheet.cell(row=currentRow, column=1).value = addDate
        # регистрация функции
        currentCell = fullStatisticsSheet.cell(row=currentRow, column=funcs[func])
        if not currentCell.value:
            currentCell.value = 0
        currentCell.value += 1

        #работа с users_statitstics
        usersStatisticsSheet = wb['users_statistics']
        # добавление нового юзера, если его еще не было
        isUserIdExists = False
        for i in range(1, usersStatisticsSheet.max_row + 1):
            if userID == usersStatisticsSheet.cell(row=i, column=1).value:
                isUserIdExists = True
                currentRow = i
                break
        if not isUserIdExists:
            currentRow = usersStatisticsSheet.max_row + 1
            forTotal = '=SUM(D{}:G{})'.format(currentRow, currentRow)
            totalCell = usersStatisticsSheet.cell(row=currentRow, column=8)
            totalCell.value = forTotal
        usersStatisticsSheet.cell(row=currentRow, column=1).value = userID

        # регистраиця функций
        usersStatisticsSheet.cell(row=currentRow, column=3).value = addDate  # last_call_date
        currentCell = usersStatisticsSheet.cell(row=currentRow, column=funcs[func] + 1)
        if func == 'start':
            currentCell.value = addDate
        else:
            if not currentCell.value:
                currentCell.value = 0
            currentCell.value += 1
        wb.save('statistics.xlsx')


Setup.setup()

try:
    import psycopg2
    con = psycopg2.connect('postgres://xoglbezchperoz:a865e0e4b54463c1cff72e04d308acbf2f959f3fe89cb18a76b45f2ac18ea9f0@ec2-54-217-234-157.eu-west-1.compute.amazonaws.com:5432/d2ba7bfo7icl95', 
                           sslmode='require')
except Exception as e:
    print(e)
else:
    print('connected')
    
