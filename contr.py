import json
from collections import namedtuple

with open("dict_contr.json", "r") as f:
    data5 = f.read()

data7 = json.loads(data5)
lst_logins = [i["login"] for i in data7]
print(lst_logins)
dict_1 = {}
dict_1.update({"page": 2})
dict_1.update({"page": 3})
print(dict_1)
