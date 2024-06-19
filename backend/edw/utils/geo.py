# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps
import time

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet

from django.db.models import Value, F, ExpressionWrapper
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from geopy.geocoders import get_geocoder_for_service
from geopy import GoogleV3, Yandex
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
            # Из документации Google
            #
            # Note: URLs must be properly encoded to be valid and are limited to 8192 characters
            # for all web services. Be aware of this limit when constructing your URLs. Note that
            # different browsers, proxies, and servers may have different URL character limits as well.
            #
            # Метод научного тыка показал, что строка из 2000 русских символов не вызывает 4xx ошибок
            # на всякий случай пусть будет 1500
            # "Адрес, состоящий из 138 знаков, стал претендентом на внесение в книгу рекордов России."
            location = _get_location_from_geocoder_by_query(query[:1500], config)
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

    address_components = getattr(_raw_obj, 'address_components', None) # google
    metaDataProperty = getattr(_raw_obj, 'metaDataProperty', None) # yandex
    if address_components is None and metaDataProperty is None:
        raise GeocoderException("{} `{}`".format(_("Postcode not found in raw data"), location))
    postalcode = None
    if address_components:
        for address_component in address_components:
            if 'postal_code' in address_component.types:
                postalcode = address_component.long_name
    if metaDataProperty:
        try:
            postalcode = metaDataProperty.GeocoderMetaData.Address.postal_code
        except AttributeError:
            pass
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
            # TODO
            # Формат адреса от Google: Народный б-р, 79Б, Белгород, Белгородская обл., Россия, 308009
            # Формат адреса от Yandex: Россия, Белгород, Народный бульвар, 79Б
            #
            # При необходимости можно из raw метадаты Яндекса отформатировать адрес как у Google,
            # собрать строку по частям: улица, дом, город, область, страна, индекс
            # То что находится в метадате, можно посмотреть так:
            # print(location.raw) <- напечатает оригинальный словарь в консоль
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

    expression_wrapper = ExpressionWrapper(expression, output_field=models.FloatField())

    queryset = model_or_queryset if isinstance(model_or_queryset, QuerySet) else model_or_queryset.objects.all()
    places = queryset.annotate(latitude=geo_to_latitude(geo_field), longitude=geo_to_longitude(geo_field)).annotate(
        distance=expression_wrapper).order_by('distance')

    return places


#==================
# Forward geocoder
#==================

YANDEX_KIND = 'house'
YANDEX_FORMAT = 'json'
YANDEX_MAPS_LANG = 'ru_RU'


def forward_geocode_yandex(config, address, referer=None):
    if not config.get('init', None) or not config['init'].get('api_key', None):
        raise ImproperlyConfigured(_('Geocoder API key was not found in GeoPy config'))

    results = []
    apikey = config['init']['api_key']
    yandex = Yandex(api_key=apikey)
    geocollection = yandex.geocode(query=address, lang=YANDEX_MAPS_LANG, exactly_one=False)
    for g in geocollection:
        address = g.raw['metaDataProperty']['GeocoderMetaData']['Address']
        point = g.raw['Point']
        results.append({
            'text': address['formatted'],
            'postal_code': address.get('postal_code', None),
            'geoposition': point['pos'],

        })

    return results

def forward_geocode_google(config, address):
    if not config.get('init', None) or not config['init'].get('api_key', None):
        raise ImproperlyConfigured(_('Geocoder API key was not found in GeoPy config'))

    results = []
    apikey = config['init']['api_key']
    google = GoogleV3(api_key=apikey)
    geocollection = google.geocode(query=address, language=YANDEX_MAPS_LANG, exactly_one=False)
    for g in geocollection:
        formatted_address = g.raw['formatted_address']
        geoposition = f'{g.longitude} {g.latitude}'
        postal_code = None
        for c in g.raw['address_components']:
            try:
                if c['types'][0] == 'postal_code':
                    postal_code = c['long_name']
            except Exception:
                pass

        results.append({
            'text': formatted_address,
            'postal_code': postal_code,
            'geoposition': geoposition,

        })

    return results


def forward_geocode(address, referer=None):
    config = getattr(settings, 'GEOPY_GEOCODER_CONFIG', None)
    if config is None or 'service' not in config:
        raise ImproperlyConfigured(_('Correct GeoPy geocoder config was not found'))

    service = config['service']

    if service == 'yandex':
        return forward_geocode_yandex(config, address, referer)
    elif service == 'googlev3':
        return forward_geocode_google(config, address)
    else:
        raise NotImplementedError(
            _('Geocoding service %(service)s is not supported') % { "service" : service })
