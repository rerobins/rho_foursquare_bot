"""
Service that will find the most commonly used locations in events (ideally these would be the most popular) that are
defined by foursquare data and return them back.
"""

import logging
import json

from rhobot.components.storage.enums import CypherFlags

from sleekxmpp.plugins.base import base_plugin
from rhobot.namespace import WGS_84, SCHEMA, GRAPH
from rdflib.namespace import RDFS
from rhobot.components.stanzas.rdf_stanza import RDFStanzaType
from rhobot.components.storage import StoragePayload
from rhobot.components.storage.namespace import NEO4J

logger = logging.getLogger(__name__)


class SearchHandler(base_plugin):
    """
    Search the database for the content
    """
    name = 'search_handler'
    description = 'Knowledge Provider'
    dependencies = {'rho_bot_storage_client', 'rho_bot_rdf_publish', 'search_venues', }

    type_requirements = {str(WGS_84.SpatialThing), }

    query = """MATCH (n:`%s`)<-[r:`http://purl.org/NET/c4dm/event.owl#place`]-(m)
                   WHERE
                      any(seeAlso in n.`%s` where seeAlso =~ '^foursquare:.*')
                   RETURN n AS node, count(r) AS rels, n.`%s` AS name
                   ORDER BY rels DESC LIMIT 10""" % (str(WGS_84.SpatialThing),
                                                     str(RDFS.seeAlso),
                                                     str(SCHEMA.name))

    def plugin_init(self):
        self.query = ' '.join(self.query.replace('\n', ' ').replace('\r', '').split())

    def post_init(self):
        super(SearchHandler, self).post_init()

        self._storage_client = self.xmpp['rho_bot_storage_client']
        self._rdf_publish = self.xmpp['rho_bot_rdf_publish']
        self._search_venues = self.xmpp['search_venues']

        self._rdf_publish.add_search_handler(self._rdf_request_message)

    def _rdf_request_message(self, rdf_payload):
        """
        Find node to do work over.
        :return:
        """
        form = rdf_payload.get('form', None)
        payload = StoragePayload(form)

        if not self._process_payload(payload):
            return None

        translation_key = dict(json.loads(CypherFlags.TRANSLATION_KEY.default))
        translation_key[str(SCHEMA.name)] = 'name'
        translation_key[str(GRAPH.degree)] = 'rels'

        logger.debug('Executing query: %s' % self.query)

        payload = StoragePayload()
        payload.add_property(key=NEO4J.cypher, value=self.query)
        payload.add_flag(CypherFlags.TRANSLATION_KEY, json.dumps(translation_key))

        promise = self._storage_client.execute_cypher(payload).then(self._process_results)

        return promise

    def _process_results(self, result):
        """
        Handle all of the results provided by the cypher query.
        :param result:
        :return:
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Found: %s results' % len(result.results))

            for res in result.results:
                logger.debug('  %s (%s)' % (res.get_column(str(SCHEMA.name)), res.get_column(str(GRAPH.degree))))

        rdf_data = self._rdf_publish.create_rdf(mtype=RDFStanzaType.SEARCH_RESPONSE, payload=result,
                                                source_name="Search Foursquare",
                                                source_command=self._search_venues.get_command_uri())

        return rdf_data

    def _process_payload(self, payload):
        """
        Determines whether the payload should be processed or not.
        :return: boolean
        """
        intersection = self.type_requirements.intersection(set(payload.types))
        return len(intersection) == len(self.type_requirements)



search_handler = SearchHandler
