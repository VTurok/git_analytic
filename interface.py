# -*- coding: utf-8 -*-
import datetime
import re
from urllib.parse import urlparse

import analytic
import settings


class ConsoleInterface:
    """
    Класс консольного интерфейса
    """

    def __init__(self):
        self.dict_valid_param = {}

    def start(self):
        """
        Функция запуска вывода интерфейса
        :return:
        """
        self._welcome_message_creator()
        self._token_controller()
        self._set_param_creator()

    def choise(self, msg):
        """
        Элемент интерфейса, спрашивающий [y\n]
        :param msg: string
        :return: bool
        """
        print(msg)
        print("Для продолжения введите [y/n]:")
        data = input()
        if data == "y":
            return True
        elif data == "n":
            return False
        else:
            self.choise("Некорректный ввод")

    def _welcome_message_creator(self):
        """
        Функция выводит приветственное сообщение при инициализации
        :return:
        """
        with open("welcome_msg.txt", "r", encoding="utf-8") as f:
            data = f.read()
        print(data)

    def _token_controller(self):
        pattern = r"\w{40}"
        if not re.match(pattern, settings.TOKEN):
            print("!!!Токен не найден. Пожалуйста укажите токен в settings.py")

    def _url_validator(self, data):
        """
        Функция валидации URL
        :param data: string
        :return: string
        """
        if data:
            tpl_data = urlparse(data)
            if tpl_data.scheme == "http" or tpl_data.scheme == "https":
                self.dict_valid_param.update({"url": tpl_data.path.strip()})
                return True
            else:
                return False
        else:
            return False

    def _time_start_validator(self, data):
        """
        Функция валидации времени начала анализа
        :param data: string
        :return: datatime
        """
        if data:
            try:
                valid_data = datetime.datetime.strptime(data, "%Y.%m.%d %H:%M:%S")
                self.dict_valid_param.update({"start_time": valid_data})
            except ValueError:
                self.dict_valid_param.update({"start_time": None})
        else:
            self.dict_valid_param.update({"start_time": None})

    def _time_stop_validator(self, data):
        """
        Функция валидации времени окончания анализа
        :param data: string
        :return: datatime
        """
        if data:
            try:
                valid_data = datetime.datetime.strptime(data, "%Y.%m.%d %H:%M:%S")
                self.dict_valid_param.update({"stop_time": valid_data})
            except ValueError:
                self.dict_valid_param.update({"stop_time": None})
        else:
            self.dict_valid_param.update({"stop_time": None})

    def _branch_validator(self, data):
        """
        Функция проверки введенной ветки
        :param data: string
        :return: string
        """
        if data:
            self.dict_valid_param.update({"branch": data})
        else:
            self.dict_valid_param.update({"branch": "master"})

    def _reader_param(self):
        """
        Функция чтения входных значений
        :return: list of strings
        """
        lst_msg = [
            "Введите URL:",
            "Введите время начала анализа:",
            "Введите время конца анализа:",
            "Введите ветку репозитория:",
        ]
        lst_input_data = []
        for i in range(4):
            print(lst_msg[i])
            data = input()
            lst_input_data.append(data)
        return lst_input_data

    def _set_param_creator(self):
        """
        Функция создания набора параметров для запуска тестирования
        :return:
        """
        lst_data = self._reader_param()
        ans = self._url_validator(lst_data[0])
        self._time_start_validator(lst_data[1])
        self._time_stop_validator(lst_data[2])
        self._branch_validator(lst_data[3])
        if ans:
            if self._show_input_data():
                self._statistic_creator()
            else:
                self._set_param_creator()
        else:
            msg = "Некорректно введены данные. Повторить ввод?"
            if self.choise(msg):
                self._set_param_creator()
            else:
                print("Выключение")

    def _show_input_data(self):
        """
        Элемент интерфейса, показывающий введенные пользователем данные
        :return: bool
        """
        lst_msg = [
            "URL репозитория:",
            "Время начала анализа:",
            "Время окончания анализа:",
            "Ветка репозитория:",
        ]
        print(lst_msg[0])
        print(self.dict_valid_param["url"])
        print(lst_msg[1])
        print(self.dict_valid_param["start_time"])
        print(lst_msg[2])
        print(self.dict_valid_param["stop_time"])
        print(lst_msg[3])
        print(self.dict_valid_param["branch"])
        return self.choise("Запустить анализ с указанными параметрами")

    def _statistic_creator(self):
        """
        Непосредственно запуск и отображение аналитики по репозиторию
        :return:
        """
        analytic_set = analytic.AnalyticsSet(
            url=self.dict_valid_param["url"],
            time_start=self.dict_valid_param["start_time"],
            time_stop=self.dict_valid_param["stop_time"],
            branch=self.dict_valid_param["branch"],
        )
        top_contrib_data = analytic_set.get_top_contrib()
        pulls_statistics = analytic_set.get_pulls_statistics(settings.PULLS_BORDER)
        issue_statistics = analytic_set.get_issues_statistics(settings.ISSUES_BORDER)
        self._contrib_render(top_contrib_data)
        self._pulls_statistics_render(pulls_statistics)
        self._issues_statistics_render(issue_statistics)

    def _contrib_render(self, data):
        """
        Элемент интерфейса, выводящий рейтинг контрибьюторов
        :param data: list of tuples
        :return:
        """
        print("Рейтинг контрибьюторов по коммитам")
        print("-" * 57)
        print("| {0:25} | {1:25} |".format("Логин", "Кол-во"))
        print("-" * 57)
        if len(data) > settings.CONTRIB_LIMIT:
            limit = settings.CONTRIB_LIMIT
        else:
            limit = len(data)
        for i in range(limit):
            print("| {0:25} | {1:25} |".format(data[i][0], data[i][1]))
        print("-" * 57)

    def _pulls_statistics_render(self, data):
        """
        Элемент интефейса, выводящий статистику по PR
        :param data: list of tuples
        :return:
        """
        print("Аналитика по pull requests")
        print("Открытые:")
        print(data.open)
        print("Закрытые:")
        print(data.closed)
        print("Старые:")
        print(data.old)

    def _issues_statistics_render(self, data):
        """
        Элемент интефейса, выводящий статистику по issues
        :param data: list of tuples
        :return:
        """
        print("Аналитика по issues")
        print("Открытые:")
        print(data.open)
        print("Закрытые:")
        print(data.closed)
        print("Старые:")
        print(data.old)
