import abc
import requests
import json
import xmltodict
import time


class Observer:
    def __init__(self):
        self.lowest_value = None
        self.source_name = None

    def update(self, observed):
        if self.lowest_value is None or self.lowest_value > observed.currency_value:

            self.source_name = observed.source
            self.lowest_value = observed.currency_value

            buyEUR(self.source_name, self.lowest_value)


class CurrencyObservable(abc.ABC):
    @abc.abstractmethod
    def register(self, callback):
        pass

    @abc.abstractmethod
    def unregister(self, callback):
        pass

    @abc.abstractmethod
    def unregister_all(self, callback):
        pass

    @abc.abstractmethod
    def get_current_currency_value(self, callback):
        pass

    @abc.abstractmethod
    def poll_for_change(self, callback):
        pass

    @abc.abstractmethod
    def update_all(self, callback):
        pass


class NbpObservable(CurrencyObservable):
    def __init__(self):
        self.callbacks = set()
        self.currency_value = None
        self.source = 'NBP'

    def register(self, callback):
        self.callbacks.add(callback)

    def unregister(self, callback):
        self.callbacks.discard(callback)

    def unregister_all(self):
        self.callbacks = set()

    def get_current_currency_value(self):
        response = requests.get(
            "http://api.nbp.pl/api/exchangerates/rates/c/eur/today/")
        return float(response.json().get('rates')[0].get('bid'))

    def poll_for_change(self):
        if self.currency_value != self.get_current_currency_value():
            self.currency_value = self.get_current_currency_value()
            self.update_all()

    def update_all(self):
        for callback in self.callbacks:
            callback(self)


class EcbObservable(CurrencyObservable):
    def __init__(self):
        self.callbacks = set()
        self.currency_value = None
        self.source = 'ECB'

    def register(self, callback):
        self.callbacks.add(callback)

    def unregister(self, callback):
        self.callbacks.discard(callback)

    def unregister_all(self):
        self.callbacks = set()

    def get_current_currency_value(self):
        response = requests.get(
            "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml")
        dict_data = xmltodict.parse(response.content)
        return float(
            dict_data['gesmes:Envelope']['Cube']['Cube']['Cube'][7]['@rate'])

    def poll_for_change(self):
        if self.currency_value != self.get_current_currency_value():
            self.currency_value = self.get_current_currency_value()
            self.update_all()

    def update_all(self):
        for callback in self.callbacks:
            callback(self)


class ExchObservable(CurrencyObservable):
    def __init__(self):
        self.callbacks = set()
        self.currency_value = None
        self.source = 'Exchangerate'

    def register(self, callback):
        self.callbacks.add(callback)

    def unregister(self, callback):
        self.callbacks.discard(callback)

    def unregister_all(self):
        self.callbacks = set()

    def get_current_currency_value(self):
        response = requests.get("https://api.exchangerate.host/latest")
        return float(response.json().get('rates').get('PLN'))

    def poll_for_change(self):
        if self.currency_value != self.get_current_currency_value():
            self.currency_value = self.get_current_currency_value()
            self.update_all()

    def update_all(self):
        for callback in self.callbacks:
            callback(self)


def buyEUR(source_name, value):
    print("Buying euro from " + source_name +
          " at the lowest rate: " + str(value))


observer = Observer()

nbp_observable = NbpObservable()
ecb_observable = EcbObservable()
exch_observable = ExchObservable()

currency_observables = []
currency_observables.append(nbp_observable)
currency_observables.append(ecb_observable)
currency_observables.append(exch_observable)

for currency_observable in currency_observables:
    currency_observable.register(observer.update)

while True:

    for currency_observable in currency_observables:
        currency_observable.poll_for_change()

    time.sleep(2.5)