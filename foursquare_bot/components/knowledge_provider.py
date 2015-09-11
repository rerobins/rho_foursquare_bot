"""
Knowledge provider that will respond to requests made by the rdf publisher or another bot.
"""
from sleekxmpp.plugins.base import base_plugin
from rhobot.components.stanzas.rdf_stanza import RDFStanzaType
from rhobot.components.storage.enums import FindFlags, FindResults
from rhobot.components.storage.client import StoragePayload
from rhobot.namespace import WGS_84
from foursquare_bot.components.utilities import get_foursquare_venue
import logging

logger = logging.getLogger(__name__)


class KnowledgeProvider(base_plugin):
    name = 'knowledge_provider'
    description = 'Knowledge Provider'
    dependencies = {'rho_bot_storage_client',
                    'rho_bot_rdf_publish',
                    'foursquare_lookup', }

    type_requirements = {str(WGS_84.SpatialThing), }

    def plugin_init(self):
        pass

    def post_init(self):
        super(KnowledgeProvider, self).post_init()

        self._storage_client = self.xmpp['rho_bot_storage_client']
        self._rdf_publish = self.xmpp['rho_bot_rdf_publish']
        self._foursquare_lookup = self.xmpp['foursquare_lookup']

        self._rdf_publish.add_request_handler(self._rdf_request_message)

    def _rdf_request_message(self, rdf_payload):
        logger.debug('Looking up knowledge')

        form = rdf_payload['form']

        payload = StoragePayload(form)

        # Determine if the payload request matches the payloads that are provided by this provider.
        intersection = self.type_requirements.intersection(set(payload.types))
        if len(intersection) == len(self.type_requirements):

            venue = get_foursquare_venue(payload)

            if venue:
                payload.add_flag(FindFlags.CREATE_IF_MISSING, True)
                promise = self._storage_client.find_nodes(payload).then(self._handle_results)

                return promise

        return None

    def _handle_results(self, result):
        if len(result.results):

            # If the node was created, then publish it to the channel, and then send it to the foursquare
            # lookup for updating.
            for res in result.results:

                # if the node was created need to mark it as being created by this bot, and notify all of listeners
                # that this node was created.
                if FindResults.CREATED.fetch_from(res.flags):
                    # Lookup the details
                    self._foursquare_lookup.schedule_lookup(res.about, create=True)

            rdf_data = self._rdf_publish.create_rdf(mtype=RDFStanzaType.SEARCH_RESPONSE, payload=result)

            return rdf_data

        return None

knowledge_provider = KnowledgeProvider
