"""
Knowledge provider that will respond to requests made by the rdf publisher or another bot.
"""
from sleekxmpp.plugins.base import base_plugin
from rhobot.components.storage.enums import FindFlags
from rhobot.components.storage.client import StoragePayload
from foursquare_bot.components.namespace import WGS_84
from foursquare_bot.components.utilities import get_foursquare_venue
import logging

logger = logging.getLogger(__name__)


class KnowledgeProvider(base_plugin):
    name = 'knowledge_provider'
    description = 'Knowledge Provider'
    dependencies = {'rho_bot_storage_client', 'rho_bot_rdf_publish', }

    type_requirements = {str(WGS_84.SpatialThing), }

    def plugin_init(self):
        pass

    def post_init(self):
        base_plugin.post_init(self)
        self.xmpp['rho_bot_rdf_publish'].add_request_handler(self._rdf_request_message)

    def _rdf_request_message(self, rdf_payload):
        logger.info('Looking up knowledge')

        form = rdf_payload['form']

        payload = StoragePayload(form)
        payload.add_flag(FindFlags.CREATE_IF_MISSING, True)

        intersection = self.type_requirements.intersection(set(payload.types()))

        if len(intersection) == len(self. type_requirements):

            venue = get_foursquare_venue(payload)

            if venue:
                results = self.xmpp['rho_bot_storage_client'].find_nodes(payload)
                if len(results.results()):
                    return results

        return None

knowledge_provider = KnowledgeProvider
