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
SEARCH_URL = "https://fias-public-service.nalog.ru/api/spas/v2.0/SearchAddressItems?search_string={0}&address_type=1"
DETAIL_URL = "https://fias-public-service.nalog.ru/api/spas/v2.0/GetAddressItemById?object_id={0}&address_type=1"

OBJ_LEVEL = 10  # region

LOCALITY_LEVELS = (6, 5)  # 5 - город, 6 - населенный пункт
REGION_LEVEL = 1  # 1 - регион


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

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',

    }

    fias_data = JSONField(verbose_name=_("FIAS data"), default={},
        help_text=_("Data returned from FIAS for defined address"))

    @cached_property
    def fias_name(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Place']['full_name']
            except (KeyError, IndexError, TypeError):
                pass
        return result

    @cached_property
    def fias_locality_name(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Locality']['full_name']
            except (KeyError, IndexError, TypeError):
                pass
        return result

    @cached_property
    def fias_locality_id(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Locality']['object_id']
            except (KeyError, IndexError, TypeError):
                pass
        return result

    @cached_property
    def fias_locality_guid(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Locality']['object_guid']
            except (KeyError, IndexError, TypeError):
                pass
        return result

    @cached_property
    def fias_region_name(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Region']['full_name']
            except (KeyError, IndexError, TypeError):
                pass
        return result

    @cached_property
    def fias_region_id(self):
        result = None
        if self.fias_data != {}:
            try:
                result = self.fias_data['Region']['object_id']
            except (KeyError, IndexError, TypeError):
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
        return _fias_validate_data in data['full_name'] if _fias_validate_data != empty else True

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
        region = None

        url = DETAIL_URL.format(object_id)
        resp = requests.get(url, headers=cls.HEADERS)
        if resp.status_code == 200 or resp.status_code == 201:
            try:
                json_data = resp.json()
            except JSONDecodeError:
                # Получен не JSON объект (чаще всего сервис недоступен, но при этом вернулся статус 200)
                pass
            else:
                try:
                    data = json_data["addresses"][0]
                    for item in data['hierarchy']:
                        if item['object_level_id'] in LOCALITY_LEVELS:
                            locality = item
                            locality.update({
                                'postal_code': data['address_details']['postal_code'],
                                'ifns_ul': data['address_details']['ifns_ul'],
                                'ifns_fl': data['address_details']['ifns_fl'],
                                'okato': data['address_details']['okato'],
                                'oktmo': data['address_details']['oktmo'],
                            })
                        elif item['object_level_id'] == REGION_LEVEL:
                            region = item
                            region.update({
                                'postal_code': data['address_details']['postal_code'],
                                'ifns_ul': data['address_details']['ifns_ul'],
                                'ifns_fl': data['address_details']['ifns_fl'],
                                'okato': data['address_details']['okato'],
                                'oktmo': data['address_details']['oktmo'],
                            })
                except (KeyError, IndexError):
                    # Вернулось не пойми что, либо нужных данных там нет (пустой json, json без Data...)
                    pass
        return locality, region

    @classmethod
    def get_fias_data_by_address(cls, address, prefixes=[]):
        """
        Метод для получения данных по адресу из ФИАС по адресу. Пример данных:
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
            resp = requests.get(url, headers=cls.HEADERS)
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
                        json_data['addresses'][0]['object_id']
                    except (KeyError, IndexError):
                        # Вернулось не пойми что, либо нужных данных там нет (например не нашлось адресов)
                        pass
                    else:
                        # Хак для того, чтоб исключить проблему номеров домов с буквами. Например: ищем дом 111,
                        # но если есть 111а - он будет первый в списке, а 111 последний
                        json_data['addresses'].reverse()
                        for item in json_data['addresses']:
                            # Проверяем что запись соответствует нашим критериям. Например, то что регион ответа совпадает
                            # с регионом портала.
                            if cls.validate_fias_data(item):
                                result['Place'] = {'object_id': item['object_id'], 'full_name': item['full_name'], 'is_active': item['is_active']}
                                result['Locality'], result['Region'] = cls.get_fias_data_by_id(item['object_id'])
                                # Если что-то нашлось, то прерываем итерирование по результату
                                break
        return result
