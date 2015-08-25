"""
Test the work of the knowledge provider tool.
"""

import unittest
from sleekxmpp.plugins.xep_0004 import Form
from rhobot.components.storage import StoragePayload
from foursquare_bot.components.namespace import WGS_84
from foursquare_bot.components.utilities import get_foursquare_venue
from rdflib.namespace import RDFS


class UtilitiesTestCase(unittest.TestCase):

    def test_request_data_with_payload(self):

        foursquare_uri = 'foursquare://venues/4be0b4f0652b0f475f607311'

        storage_payload = StoragePayload(Form())

        storage_payload.add_type(WGS_84.SpatialThing)
        storage_payload.add_property(RDFS.seeAlso, foursquare_uri)

        result = get_foursquare_venue(storage_payload)

        self.assertEqual(result, foursquare_uri.split('/')[-1])
