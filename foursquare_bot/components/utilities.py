"""
Collection of utilities for the foursquare provider.
"""
# TODO: build translation key between foursquare categories and dbpedia.org/ontology
# See: http://www.geonames.org/ontology/mappings_v3.01.rdf
from foursquare_bot.components.namespace import WGS_84, SCHEMA
from rdflib.namespace import RDFS
import urlparse


def get_foursquare_venue(payload):
    """
    Determine whether the payload is for a foursquare data source or not.
    :param payload: payload to test.
    :return:
    """
    venue = None
    if str(WGS_84.SpatialThing) in payload.types():
        properties = payload.properties()
        see_alsos = properties.get(str(RDFS.seeAlso), None)
        if see_alsos:
            for see_also in see_alsos:
                venue = get_foursquare_venue_from_url(see_also)
                if venue:
                    break

    return venue


def get_foursquare_venue_from_url(url):
    """
    Parse the venue from the url value and get the venue identifier.
    :param url:
    :return:
    """
    venue = None
    url_components = urlparse.urlparse(url)

    if url_components.scheme == 'foursquare' and url_components.netloc == 'venues':
        venue = url_components.path.split('/')[1]

    return venue


def foursquare_to_storage(foursquare, storage):
    """
    Translate the foursquare details of a venue into a storage object.
    :param foursquare: foursquare details.
    :param storage: storage object.
    :return: storage object.
    """
    storage.add_type(WGS_84.SpatialThing)
    storage.add_property(RDFS.seeAlso, 'foursquare://venues/%s' % foursquare['id'])
    storage.add_property(SCHEMA.name, foursquare['name'])

    location = foursquare['location']
    if 'lat' in location and 'lng' in location:
        storage.add_property(WGS_84.lat, location['lat'])
        storage.add_property(WGS_84.long, location['lng'])

    return storage
