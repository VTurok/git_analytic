# -*- coding: utf-8 -*-
class InputDataError(Exception):
    """
    Класс ошибки входных данных
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
