import datetime
import collections

class CashKey:
    def __init__(self, name, r_type):
        self.name = name
        self.r_type = r_type

    def __key(self):
        return self.name, self.r_type

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(self, type(other)) and self.__key() == other.__key()


class CashValue:
    def __init__(self, data, expiration_time):
        self.data = data
        self.expiration_time = expiration_time

    def __eq__(self, other):
        return self.data == other.data


class Cash:
    def __init__(self):
        self.cash = collections.defaultdict(list)

    def add_record(self, rr):
        key = CashKey(rr.url, rr.r_type)
        t_delta = datetime.timedelta(seconds=rr.ttl)
        expiration_time = datetime.datetime.now() + t_delta
        value = CashValue(rr.data, expiration_time)
        if value not in self.cash[key]:
            self.cash[key].append(value)

    def get_answer(self, url, r_type):
        key = CashKey(url, r_type)
        self._check_ttl(key)
        if not self.cash[key]:
            return None
        return [v.data for v in self.cash[key]]

    def _check_ttl(self, key):
        for value in self.cash[key]:
            if datetime.datetime.now() > value.expiration_time:
                self.cash[key].remove(value)

    def make_serializable(self):
        jsonable_list = []
        for key, values in self.cash.items():
            if not values:
                continue
            value_dict = {}
            key_tuple = (key.name, key.r_type)
            value_dict["key"] = key_tuple
            jsonable_values = []
            for value in values:
                value_tuple = (value.data, value.expiration_time.timetuple()[0:6])
                jsonable_values.append(value_tuple)
            value_dict["value"] = jsonable_values
            jsonable_list.append(value_dict)
        return jsonable_list


    @staticmethod
    def get_cash_from_json(json_list):
        cash = Cash()
        for pair in json_list:
            key_j = pair["key"]
            values_j = pair["value"]
            key = CashKey(key_j[0], key_j[1])
            for value_j in values_j:
                expiration_time = datetime.datetime(*(value_j[1]))
                if datetime.datetime.now() > expiration_time:
                    continue
                value = CashValue(value_j[0], expiration_time)
                cash.cash[key].append(value)
        return cash

    def __str__(self):
        s = ""
        for k in self.cash:
            s += f"{(k.name, k.r_type)}: {', '.join([v.data for v in self.cash[k]])}; "
        return s








