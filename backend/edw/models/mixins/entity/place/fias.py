# -*- coding: utf-8 -*-

import re
import requests
from jsonfield.fields import JSONField
from simplejson import JSONDecodeError
from rest_framework.fields import empty

from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property

from edw.models.mixins import ModelMixin


#==================================================================================================
#
#==================================================================================================
SEARCH_URL = "https://fias.nalog.ru/Search/Searching?text={0}"
DETAIL_URL = "https://fias.nalog.ru/AddressObjectDetailPage/ObjHierarchyInfoGrid?objId={0}&objLvl={1}&tabStripLvl={2}"

OBJ_LEVEL = 10  # region

LOCALITY_LEVELS = (6, 5)  # 5 - город, 6 - населенный пункт
REGION_LEVEL = 1  # 1 - регион

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}


class FIASMixin(ModelMixin):
    """
    Миксин для работы с данными из ФИАС. Добавляет в модель методы получения нужных полей из сохраненного ответа
    """
    FIAS_VALIDATE_DATA = empty
    FIAS_ADDRESS_REPLACERS = [
        ('г\.', 'город '),
        ('пр\.', 'проспект '),
        ('просп\.\,', 'проспект,'),
        ('обл\.\,', 'область,'),
        ('обл\.', 'область '),
        ('ул\.', 'улица '),
        ('пер\. ', 'переулок '),
        ('м\-н.', 'микрорайон '),
        ('м\-н', 'микрорайон'),
    ]

    fias_data = JSONField(verbose_name=_("FIAS data"), default={},
        help_text=_("Data returned from FIAS for defined address"))

    @cached_property
    def fias_name(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Place']['Name']
            except (KeyError, IndexError):
                pass
        return result

    @cached_property
    def fias_locality_name(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Locality']['Name']
            except (KeyError, IndexError):
                pass
        return result

    @cached_property
    def fias_locality_id(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Locality']['objId']
            except (KeyError, IndexError):
                pass
        return result

    @cached_property
    def fias_locality_guid(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Locality']['GUID']
            except (KeyError, IndexError):
                pass
        return result

    @cached_property
    def fias_region_name(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Region']['Name']
            except (KeyError, IndexError):
                pass
        return result

    @cached_property
    def fias_region_id(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Region']['objId']
            except (KeyError, IndexError):
                pass
        return result

    @classmethod
    def validate_fias_data(cls, data):
        # Базовый метод, возвращает True если в данных в 'PresentRow' присутствует строка cls.FIAS_VALIDATE_DATA
        # или если она не установлена. То есть если не установлено то считаем любые данные корректными. Кешируем
        # проверочные данные в классе.
        _fias_validate_data = getattr(cls, '_fias_validate_data', empty)
        if _fias_validate_data == empty:
            _fias_validate_data = cls.FIAS_VALIDATE_DATA
            cls._fias_validate_data = _fias_validate_data
        return _fias_validate_data in data['PresentRow'] if _fias_validate_data != empty else True

    @classmethod
    def fias_prepare_address(cls, address):
        # Метод модифицирует адресную строку для улучшения поиска на сервере ФИАС.
        # ФИАС не умеет корректно искать такие адреса поэтому просто выходим
        if 'Unnamed Road' in address:
            return
        # Очищаем гугл адреса вида `5439+8R Город, Область, Россия`, оставляем только корректный русскоязычный адрес
        search_name = address
        match = re.search('(.*\+.[a-zA-Z0-9])', search_name)
        if match:
            search_name = search_name.replace(f'{match.group(1)} ', '')
        # Очищаем индекс, так как он мешает
        match = re.search('(,.?\d{6})', search_name)
        if match:
            search_name = search_name.replace(f'{match.group(1)}', '')
        # Добавляем слово дом к номеру
        match = re.search('(\d.{,5})', search_name)
        if match:
            search_name = search_name.replace(f'{match.group(1)}', f'дом {match.group(1)}')
        # Выполняем замену по подстановочному списку
        for replacer in cls.FIAS_ADDRESS_REPLACERS:
            search_name = re.sub(replacer[0], replacer[1], search_name)
        return re.sub(' +', ' ', search_name)

    @classmethod
    def get_fias_data_by_id(cls, object_id):
        """
        Метод для получения данных по адресу из ФИАС по идентификатору адресного объекта (не GUID!!).
        Возвращает:
        'locality' - данные по населенному пункту или городу, которому принадлежит адресный объект.
        'region' - данные по региону которому принадлежит данный населенный пункт или город
        """
        locality = None
        for lvl in LOCALITY_LEVELS:
            # Циклом перебираем потенциальные уровни начиная с 'Населенный пункт'
            url = DETAIL_URL.format(object_id, OBJ_LEVEL, lvl)
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code == 200 or resp.status_code == 201:
                try:
                    json_data = resp.json()
                except JSONDecodeError:
                    # Получен не JSON объект (чаще всего сервис недоступен, но при этом вернулся статус 200)
                    pass
                else:
                    try:
                        data = json_data["Data"]
                        if len(data) > 0:
                            locality = data[0]
                            break
                    except (KeyError, IndexError):
                        # Вернулось не пойми что, либо нужных данных там нет (пустой json, json без Data...)
                        pass

        # получаем регион
        region = None
        url = DETAIL_URL.format(object_id, OBJ_LEVEL, REGION_LEVEL)
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200 or resp.status_code == 201:
            try:
                json_data = resp.json()
            except JSONDecodeError:
                # Получен не JSON объект (чаще всего сервис недоступен, но при этом вернулся статус 200)
                pass
            else:
                try:
                    data = json_data["Data"]
                    if len(data) > 0:
                        region = data[0]
                except (KeyError, IndexError):
                    # Вернулось не пойми что, либо нужных данных там нет (пустой json, json без Data...)
                    pass
        return locality, region

    @classmethod
    def get_fias_data_by_address(cls, address, prefixes=[]):
        """
        Метод для получения данных по адресу из ФИАС по адресу. Пример данных:
        {
            'Place': {
              'ObjectId': 14852881,
              'PresentRow': 'Республика Бурятия, город Улан-Удэ, улица Ранжурова, дом 6А',
              'IsActive': True
            },
            'Locality': {
              'objId': 53140,
              'Name': 'город Улан-Удэ',
              'PostalCode': '',
              'IFNSUL': '',
              'IFNSFL': '',
              'OKATO': '81401000000',
              'OKTMO': '81701000001',
              'GUID': '9fdcc25f-a3d0-4f28-8b61-40648d099065',
              'ReestrCode': '817010000010000000001',
              'CadastrCode': '',
              'Code': '0300000100000',
              'ObjectLevelId': 10,
              'HasChild': False,
              'IsActual': True
            },
            'Region': {
              'objId': 53099,
              'Name': 'Республика Бурятия',
              'PostalCode': '671000',
              'IFNSUL': '0300',
              'IFNSFL': '0300',
              'OKATO': '81000000000',
              'OKTMO': '81000000',
              'GUID': 'a84ebed3-153d-4ba9-8532-8bdf879e1f5a',
              'ReestrCode': '810000000000000000001',
              'CadastrCode': '',
              'Code': '0300000000000',
              'ObjectLevelId': 10,
              'HasChild': False,
              'IsActual': True
            }
        }
        'Place' - данные по адресному объекту
        'Locality' - данные по населенному пункту или городу, которому принадлежит адресный объект
        'Region' - данные по региону которому принадлежит данный населенный пункт или город
        """
        # Преобразовываем адрес согласно особенностям поиска ФИАС, если вернулась пустая строка - адрес нельзя искать
        address = cls.fias_prepare_address(address)
        # Формируем результат для возврата
        result = {}
        if address:
            # Добавляем к адресу уточняющие данные, если их там нет, например prefixes ['N-ская область', 'город N-ск']
            for prefix in prefixes:
                if not prefix in address:
                    address = f'{prefix}, {address}'
            # Формируем запрос получения данных по адресу из ФИАС. Находится
            url = SEARCH_URL.format(address)
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code == 200 or resp.status_code == 201:
                try:
                    json_data = resp.json()
                except JSONDecodeError:
                    # Получен не JSON объект (чаще всего сервис недоступен, но при этом вернулся статус 200)
                    pass
                else:
                    try:
                        # Берем первый адрес в списке и из него получаем ID адресного объекта, для проверки того
                        # что получены корректные данные
                        json_data[0]['ObjectId']
                    except (KeyError, IndexError):
                        # Вернулось не пойми что, либо нужных данных там нет (например не нашлось адресов)
                        pass
                    else:
                        # Хак для того, чтоб исключить проблему номеров домов с буквами. Например: ищем дом 111,
                        # но если есть 111а - он будет первый в списке, а 111 последний
                        json_data.reverse()
                        for item in json_data:
                            # Проверяем что запись соответствует нашим критериям. Например, то что регион ответа совпадает
                            # с регионом портала.
                            if cls.validate_fias_data(item):
                                result['Place'] = item
                                result['Locality'], result['Region'] = cls.get_fias_data_by_id(item['ObjectId'])
                                # Если что-то нашлось, то прерываем итерирование по результату
                                break
        return result
