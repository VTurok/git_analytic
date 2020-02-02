# -*- coding: utf-8 -*-
import interface
import error

if __name__ == "__main__":
    while True:
        intr = interface.ConsoleInterface()
        try:
            intr.start()
            print("Анализ завершен")
        except error.InputDataError as e:
            print(e)
            print("Анализ не удался")
        finally:
            if not intr.choise("Хотите выполнить еще один анализ"):
                break
