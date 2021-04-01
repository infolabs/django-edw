# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from functools import wraps
import time
import requests

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet

from django.db.models import Value, F
from django.utils.translation import ugettext_lazy as _

from geopy.geocoders import get_geocoder_for_service
from geopy.exc import GeocoderQuotaExceeded

from edw.utils.common import dict2obj

from edw.models.expressions import (
    CharLength, Position, Substring, Cast, Decimal, Sin, Cos, Acos, Radians
)

#=================================================
# Geocoder exception
#=================================================
class GeocoderException(Exception):
    pass


#=================================================
# Geocoder request retry decorator
#=================================================
GEOCODER_REQUEST_RETRY_DEFAULT_TIMEOUT = 2
GEOCODER_REQUEST_RETRY_DEFAULT_ATTEMPTS = 3

def geocoder_request_retry(attempts, timeout=GEOCODER_REQUEST_RETRY_DEFAULT_TIMEOUT):
    def geocoder_request_retry_decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            i = 0
            success = False
            while not success and i < attempts:
                i += 1
                try:
                    result = func(*args, **kwargs)
                except GeocoderQuotaExceeded:
                    time.sleep(timeout)
                    continue
                else:
                    success = True
            if i == attempts:
                raise GeocoderException(_('Daily requests limit has been reached'))
            return result
        return func_wrapper
    return geocoder_request_retry_decorator


#=================================================
# Get location from geocoder by geoposition
#=================================================
@geocoder_request_retry(GEOCODER_REQUEST_RETRY_DEFAULT_ATTEMPTS)
def _get_location_from_geocoder_by_geoposition(geoposition, config):
    '''
    local function for reverse location by geoposition
    :param geoposition: geoposition object: string format: "altitude, longitude"
    :param config: dict of params for geocoder
    :return: location: location object
    '''
    location = None
    geocoder = get_geocoder_for_service(config.get('service', None))
    if geocoder is not None:
        geolocator = geocoder(**config.get('init', {}))
        location = geolocator.reverse(
            str(geoposition),
            **config.get('reverse', {})
        )
    return location


#=================================================
# Get location from geocoder by query
#=================================================
@geocoder_request_retry(GEOCODER_REQUEST_RETRY_DEFAULT_ATTEMPTS)
def _get_location_from_geocoder_by_query(query, config):
    '''
    local function for reverse location by query
    :param query: query: query string for reversing, exapmle: Moscow
    :param config: dict of params for geocoder
    :return: location: location object
    '''
    location = None
    geocoder = get_geocoder_for_service(config.get('service', None))
    if geocoder is not None:
        geolocator = geocoder(**config.get('init', {}))
        location = geolocator.geocode(
            query,
            **config.get('reverse', {})
        )
    return location


#=================================================
# Get location from configured geocoder
#=================================================
def get_location_from_geocoder(geoposition=None, query=None):
    '''
    Get location from geocoder by geoposition or query string
    :param geoposition: geoposition object: string in format "altitude, longitude"
    :param query: query string for reversing, exapmle: Moscow
    :return: location: location object
    '''
    config = getattr(settings, 'GEOPY_GEOCODER_CONFIG', None)
    if config is not None:
        if geoposition is not None:
            location = _get_location_from_geocoder_by_geoposition(geoposition, config)
        elif query is not None:
            location = _get_location_from_geocoder_by_query(query, config)
        else:
            raise GeocoderException(_('Both of geoposition and query can`t be None'))
    else:
        raise GeocoderException(_('Geocoder not configured yet. Confirm your GEOPY_GEOCODER_CONFIG settings is valid'))
    return location


#=================================================
# Get location postcode
#=================================================
def get_postcode(location):
    '''
    Get location postcode
    :param location: location object
    :return: postcode: varchar(16)
    '''
    if location and hasattr(location, 'raw'):
        _raw_obj = dict2obj(location.raw)
    else:
        raise GeocoderException(_("Expect location"))
    try:
        address_components = _raw_obj.address_components # google
    except:
        raise GeocoderException("{} `{}`".format(_("Postcode not found in raw data"), location))
    postalcode = None
    for address_component in address_components:
        if 'postal_code' in address_component.types:
            postalcode = address_component.long_name
    if not postalcode:
        raise GeocoderException("{} `{}`".format(_("Postcode not found in raw data"), location))
    return postalcode


#=================================================
# Get location name
#=================================================
def get_name(location):
    '''
    Get location name
    :param location: location object
    :return: name: varchar(255)
    '''
    if location and hasattr(location, 'raw'):
        _raw_obj = dict2obj(location.raw)
    else:
        raise GeocoderException(_("Expect location"))
    name = None
    try:
        name = _raw_obj.formatted_address  # google
    except:
        try:
            name = _raw_obj.metaDataProperty.GeocoderMetaData.text  # yandex
        except:
            pass
    return name


#=================================================
# Get closest model utils
#=================================================
EARTH_RADIUS_METERS = 6378137


def lat_lon_substring(geo_field):
    return Substring(
        F(geo_field),
        Position(Value(","), F(geo_field)) + 1,
        CharLength(F(geo_field))
    )


def geo_to_latitude(geo_field):
    return Cast(
        Substring(
            lat_lon_substring(geo_field),
            1,
            Position(Value(","), lat_lon_substring(geo_field)) - 1
        ),
        Decimal(12, 10),
        output_field=models.FloatField()
    )


def geo_to_longitude(geo_field):
    return Cast(
        Substring(
            lat_lon_substring(geo_field),
            Position(Value(","), lat_lon_substring(geo_field)) + 1,
            CharLength(lat_lon_substring(geo_field))
        ),
        Decimal(13, 10),
        output_field=models.FloatField()
    )


def get_closest(model_or_queryset, geo_field, latitude, longitude):
    from_lat = Radians(latitude)
    from_lon = Radians(longitude)
    to_lat = Radians(F('latitude'))
    to_lon = Radians(F('longitude'))

    expression = EARTH_RADIUS_METERS * Acos(Cos(from_lat) * Cos(to_lat) *
                    Cos(to_lon - from_lon) + Sin(from_lat) * Sin(to_lat))
    queryset = model_or_queryset if isinstance(model_or_queryset, QuerySet) else model_or_queryset.objects.all()
    places = queryset.annotate(latitude=geo_to_latitude(geo_field), longitude=geo_to_longitude(geo_field)).annotate(
        distance=expression).order_by('distance')

    return places


def get_fias_data_by_address(address):
    SEARCH_URL = "https://fias.nalog.ru/Search/Searching?text={0}"
    DETAIL_URL = "https://fias.nalog.ru/AddressObjectDetailPage/ObjHierarchyInfoGrid?objId={0}&objLvl={1}&tabStripLvl={2}"

    OBJ_LEVEL = 10
    # 1 - регион
    # 5 - город
    # 6 - населенный пункт
    LOCALITY_LEVELS = (6, 5)
    REGION_LEVEL = 1

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    result = {}
    url = SEARCH_URL.format(address)
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200 or resp.status_code == 201:
        json_data = resp.json()
        try:
            # берем первый попавшшийся адрес и из него получаем ID адресного объекта
            address_code = json_data[0]['ObjectId']
        except (KeyError, IndexError):
            # Вернулось не пойми что
            pass
        else:
            for lvl in LOCALITY_LEVELS:
                # циклом перебираем потенциальные уровни начиная с Населенный пункт
                url = DETAIL_URL.format(address_code, OBJ_LEVEL, lvl)
                resp = requests.get(url, headers=HEADERS)
                if resp.status_code == 200 or resp.status_code == 201:
                    json_data = resp.json()
                    try:
                        data = json_data["Data"]
                        if len(data) > 0:
                            result['locality'] = data[0]
                            break
                    except (KeyError, IndexError):
                        # Вернулось не пойми что
                        pass
            # получаем регион
            url = DETAIL_URL.format(address_code, OBJ_LEVEL, REGION_LEVEL)
            resp = requests.get(url, headers=HEADERS)
            if resp.status_code == 200 or resp.status_code == 201:
                json_data = resp.json()
                try:
                    data = json_data["Data"]
                    if len(data) > 0:
                        result['region'] = data[0]
                except (KeyError, IndexError):
                    # Вернулось не пойми что
                    pass
    return result

