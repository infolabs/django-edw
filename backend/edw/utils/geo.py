# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models import Value, F
from django.utils.translation import ugettext_lazy as _

from geopy.geocoders import get_geocoder_for_service

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
# Get location from geocoder by geoposition
#=================================================
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
def _get_location_from_geocoder_by_query(query, config):
    '''
    local function for reverse location by query
    :param query: query: query string for reversing, exapmle: Moscow
    :param config: dict of params for geocoder
    :return: location: location object
    '''
    # todo: реализовать функционал получения location по названию
    return None


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


def geo_to_latitude(geo_field):
    return Cast(
        Substring(
            F(geo_field),
            1,
            Position(Value(","), F(geo_field)) - 1
        ),
        Decimal(12, 10),
        output_field=models.FloatField()
    )


def geo_to_longitude(geo_field):
    return Cast(
        Substring(
            F(geo_field),
            Position(Value(","), F(geo_field)) + 1,
            CharLength(F(geo_field))
        ),
        Decimal(13, 10),
        output_field=models.FloatField()
    )


def get_closest(model, geo_field, latitude, longitude):

    from_lat = Radians(latitude)
    from_lon = Radians(longitude)
    to_lat = Radians(F('latitude'))
    to_lon = Radians(F('longitude'))

    expression = EARTH_RADIUS_METERS * Acos(Cos(from_lat) * Cos(to_lat) *
                    Cos(to_lon - from_lon) + Sin(from_lat) * Sin(to_lat))

    places = model.objects.all()\
        .annotate(latitude=geo_to_latitude(geo_field), longitude=geo_to_longitude(geo_field))\
        .annotate(distance=expression).order_by('distance')

    return places[0] if len(places) else None
