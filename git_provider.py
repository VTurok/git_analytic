# -*- coding: utf-8 -*-
import re
import requests
from requests.auth import AuthBase

import settings
import error


class TokenAuth(requests.auth.AuthBase):
    """
    Класс авторизации через токен
    """

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "{0}".format(self.token)
        return r


class Request:
    """
    Класс запроса
    """

    def __init__(self, url, dict_param=None):
        self.url = self._url_creator(url)
        self.dict_param = dict_param
        self.resp = self._get_response()

    def get_data(self):
        """
        Функция получения данных из запроса
        :return:
        """
        return self.resp.json()

    def _get_response(self):
        """
        Функция получения ответа
        :return:
        """
        # Тут ее нужно еще конкретно доработать
        try:
            token = "token {0}".format(settings.TOKEN)
            response = requests.get(
                self.url, params=self.dict_param, auth=TokenAuth(token)
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            # Тут по хорошему нужно отлавливать закончившиеся запросы и посылать это пользователю, мол попробуй позже
            raise error.InputDataError(e)

    def _url_creator(self, url):
        """
        Класс создания url
        :param url:
        :return: string
        """
        ans = "{0}{1}".format(settings.GIT_URL, url)
        return ans

    def get_http_status(self):
        """
        Функция получения http статуса ответа
        :return: int
        """
        try:
            ans = self.resp.status_code
        except AttributeError:
            raise error.InputDataError("Что-то не так с введенными данными")
        return ans

    def _get_http_header(self, header_name):
        """
        Функция получения заголовков из ответа
        :param header_name: string
        :return:
        """
        if header_name in self.resp.headers.keys():
            return self.resp.headers[header_name]
        else:
            return None

    def get_page_qty(self):
        """
        Функция получения кол-ва страниц
        :return: int
        """
        http_header = self._get_http_header("Link")
        if http_header is not None:
            return self._link_header_handler(http_header)
        else:
            return None

    def _link_header_handler(self, str_header):
        """
        Обработчик http заголовка, извлекающий из него кол-во страниц
        :param str_header:
        :return: int
        """
        lst_header = str_header.split()
        pattern = r"[0-9]+>;$"
        ans = int(re.search(pattern, lst_header[2]).group().strip(">;"))
        return ans
