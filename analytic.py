# -*- coding: utf-8 -*-
import re
import datetime
from collections import namedtuple

import git_provider
import error


class AnalyticsSet:
    """
    Класс объекта запроса
    """

    def __init__(self, url, time_start=None, time_stop=None, branch="master"):
        self.repo = self._url_validator(url)
        self.time = self._time_validator(time_start, time_stop)
        self.branch = self._branch_validator(branch)

    def _url_validator(self, url):
        """
        Функция валидирования введенного url
        :param url: string
        :return: string
        """
        pattern = r"\/\w+\/\w+\/$"
        ans = re.search(pattern, url).group().strip("/")
        resp = git_provider.Request(ans)
        if resp.get_http_status() == 200:
            return ans
        else:
            raise error.InputDataError("Неверный url")

    def _time_validator(self, time_start, time_stop):
        """
        Функция валидирования временных рамок
        :param time_start: string or None
        :param time_stop: string or None
        :return: namedtuple
        """
        if time_start is not None and time_stop is not None:
            if time_stop.timestamp() - time_start.timestamp() < 0:
                raise error.InputDataError(
                    "Временной интервал для анализа отрицательный."
                )
        time = namedtuple("Time", "start stop")
        return time(time_start, time_stop)

    def _branch_validator(self, branch):
        """
        Функция валидирования ветки репозитория
        :param branch: string
        :return: string
        """
        url = "{0}{1}{2}".format(self.repo, "/branches/", branch)
        req = git_provider.Request(url)
        if req.get_http_status() == 200:
            return branch
        else:
            raise error.InputDataError("Данная ветка отсутствует")

    def get_top_contrib(self):
        """
        Функция получения рейтинга контрибьюторов по количеству коммитов
        :return: list of tuples
        """
        data = TopContributors(self.repo, self.time, branch=self.branch)
        return data.get_sorted_set()

    def get_pulls_statistics(self, border):
        """
        Функция получения статистики по pull requests
        :param border: int
        :return: tuple
        """
        data = PullsAnalytics(self.repo, self.time, branch=self.branch)
        return data.get_pulls_stat(border)

    def get_issues_statistics(self, border):
        """
        Функция получения статистики по issues
        :param border: int
        :return: tuple
        """
        data = IssueAnalytics(self.repo, self.time, branch=self.branch)
        return data.get_issues_stat(border)


class BaseAnalyticParamClass:
    """
    Родительский класс получения одного элемента аналитики
    """

    def __init__(self, repo, time, branch="master"):
        self.repo = repo
        self.time = time
        self.branch = branch

    def _get_start_data(self, url, dict_param):
        """
        Функция получения количества страниц в пагинации и данных с первого листа
        :param url:
        :param dict_param:
        :return:
        """
        ans = git_provider.Request(url, dict_param)
        return ans.get_page_qty(), ans.get_data()

    def _get_last_page_len_list(self, url, dict_param):
        """
        Функция получения количества элементов на последнем листе
        :param url:
        :return:
        """
        ans = git_provider.Request(url, dict_param)
        return len(ans.get_data())

    def _get_list_all(self, url, dict_param):
        """
        Функция извлечения всех данных из ответа с пагинацией
        :param url:
        :param dict_param:
        :return: list of dicts
        """
        n, data = self._get_start_data(url, dict_param)
        if n is not None:
            for i in range(2, n + 1):
                dict_param.update({"page": i})
                ans = git_provider.Request(url, dict_param)
                data.extend(ans.get_data())
            return data
        else:
            return data

    def _get_timestamp(self, data):
        """
        Получение временой метки из объекта datatime
        :param data:
        :return: float
        """
        d = datetime.datetime.strptime(data, "%Y-%m-%dT%H:%M:%SZ")
        return d.timestamp()

    def _get_all(self, url, param):
        """
        Получение всех данных, пришедших от сервера
        :param url: string
        :param param: string
        :return: list of dicts
        """
        dict_param = {"per_page": 100, "state": param}
        return self._get_list_all(url, dict_param)

    def _get_qty(self, url, param):
        # Тут я может не до конца разобрался с api или там в принципе по другому нельзя,
        # вообщем из-за пагинации только как-то так
        """
        Получение общего количества элементов пришедших с сервера
        :param url: string
        :param param: string
        :return: int
        """
        dict_param = {"per_page": 100, "state": param}
        n, data = self._get_start_data(url, dict_param)
        if not data:
            qty = 0
            return qty
        else:
            if n is not None:
                dict_param.update({"page": n})
                qty = 100 * (n - 1) + self._get_last_page_len_list(url, dict_param)
            else:
                qty = len(data)
            return qty


class TopContributors(BaseAnalyticParamClass):
    """
    Класс анализа контрибьюторов
    """

    def _get_list_all_contributors(self):
        """
        Функция получения списка всех контрибьюторов
        :return: list of strings
        """
        url = "{0}{1}".format(self.repo, "/contributors")
        dict_param = {"per_page": 100}
        data = self._get_list_all(url, dict_param)
        return self._login_contributor_extractor(data)

    def _login_contributor_extractor(self, lst_data):
        """
        Функция для извлечения логина контрибутора
        :param lst_data: dict
        :return: list of strings
        """
        lst_logins = [i.get("login") for i in lst_data]
        return lst_logins

    def _get_commits_qty_for_one_contributor(self, name, dict_contributors):
        """
        Функция для получения общего количества коммитов определенного контрибьютора в определенную ветку
        :param name: str
        :param dict_contributors: dict
        :return: int
        """
        url = "{0}{1}".format(self.repo, "/commits")
        dict_param = {"per_page": 100, "author": name, "sha": self.branch}
        if self.time.start is not None:
            dict_param.update({"since": self.time.start.strftime("%Y-%m-%dT%H:%M:%SZ")})
        if self.time.stop is not None:
            dict_param.update({"until": self.time.stop.strftime("%Y-%m-%dT%H:%M:%SZ")})
        n, data = self._get_start_data(url, dict_param)
        if not data:
            dict_contributors.update({name: 0})
        else:
            if n is not None:
                dict_param.update({"page": n})
                qty = 100 * (n - 1) + self._get_last_page_len_list(url, dict_param)
                dict_contributors.update({name: qty})
            else:
                qty = len(data)
                dict_contributors.update({name: qty})

    def _get_set(self):
        """
        Функция получения статистики по рейтингу контрибьюторов
        :return: dict
        """
        dict_contributors = {}
        for i in self._get_list_all_contributors():
            self._get_commits_qty_for_one_contributor(i, dict_contributors)
        return dict_contributors

    def get_sorted_set(self):
        """
        Функция получения отсортированной статистики по рейтингу контрибьюторов
        :return: list of tuples
        """
        dict_contributors = self._get_set()
        lst_items = list(dict_contributors.items())
        lst_items.sort(key=lambda i: i[1], reverse=True)
        return lst_items


class PullsAnalytics(BaseAnalyticParamClass):
    """
    Класс для анализа Pull requests
    """

    def _pulls_time_param_extractor(self, data):
        """
        Функция извлечения параметров pull request из словаря
        :param data: dict
        :return: tuple
        """
        fields = ["created", "updated", "closed", "merged"]
        pull = namedtuple("Pull", fields)
        return pull(
            data.get("created_at"), data.get("updated_at"), data.get("closed_at"), data.get("merged_at")
        )

    def _pulls_classifier(self, old_border):
        """
        Функция сбора и классификации статистики по pull requests
        :param old_border: int
        :return: dict
        """
        url = "{0}{1}".format(self.repo, "/pulls")
        now_timestamp = datetime.datetime.now()
        float_now_timestamp = now_timestamp.timestamp()
        dict_pull_classified = {"opened_all": 0, "closed_all": 0, "old_all": 0}
        lst_open_pulls = self._get_all(url, "open")
        dict_pull_classified["open_all"] = len(lst_open_pulls)
        for element in lst_open_pulls:
            pull = self._pulls_time_param_extractor(element)
            created_timestamp = self._get_timestamp(pull.created)
            if float_now_timestamp - created_timestamp >= old_border:
                dict_pull_classified["old_all"] += 1
        dict_pull_classified["closed_all"] = self._get_qty(url, "closed")
        return dict_pull_classified

    def get_pulls_stat(self, border):
        """
        Функция получения статистики по pull requests
        :param border: int
        :return: tuple
        """
        border_sec = 3600 * 24 * border
        data = self._pulls_classifier(border_sec)
        pull_stat = namedtuple("PullStat", "open closed old")
        return pull_stat(data["open_all"], data["closed_all"], data["old_all"])


class IssueAnalytics(BaseAnalyticParamClass):
    """
    Класс для анализа Issues
    """

    def _issues_time_param_extractor(self, data):
        """
        Функция извлечения параметров issue из словаря
        :param data: dict
        :return: tuple
        """
        fields = ["created", "updated", "closed"]
        issue = namedtuple("Issue", fields)
        return issue(data["created_at"], data["updated_at"], data["closed_at"])

    def _issues_classifier(self, old_border):
        """
        Функция сбора и классификации статистики по Issues
        :param old_border: int
        :return: dict
        """
        url = "{0}{1}".format(self.repo, "/issues")
        now_timestamp = datetime.datetime.now()
        float_now_timestamp = now_timestamp.timestamp()
        dict_issue_classified = {"opened_all": 0, "closed_all": 0, "old_all": 0}
        lst_open_issues = self._get_all(url, "open")
        dict_issue_classified["open_all"] = len(lst_open_issues)
        for element in lst_open_issues:
            pull = self._issues_time_param_extractor(element)
            created_timestamp = self._get_timestamp(pull.created)
            if float_now_timestamp - created_timestamp >= old_border:
                dict_issue_classified["old_all"] += 1
        dict_issue_classified["closed_all"] = self._get_qty(url, "closed")
        return dict_issue_classified

    def get_issues_stat(self, border):
        """
        Функция получения статистики по Issues
        :param border: int
        :return: tuple
        """
        border_sec = 3600 * 24 * border
        data = self._issues_classifier(border_sec)
        issue_stat = namedtuple("IssueStat", "open closed old")
        return issue_stat(data["open_all"], data["closed_all"], data["old_all"])
