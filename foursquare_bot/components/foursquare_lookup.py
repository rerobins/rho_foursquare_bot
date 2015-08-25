from sleekxmpp.plugins.base import base_plugin
from rhobot.components.configuration import BotConfiguration
from foursquare_bot.components.configuration_enums import CLIENT_SECRET_KEY, IDENTIFIER_KEY
from foursquare_bot.components.utilities import get_foursquare_venue_from_url, foursquare_to_storage
import logging
import foursquare
from rdflib.namespace import RDFS

logger = logging.getLogger(__name__)


class FoursquareLookup(base_plugin):
    name = 'foursquare_lookup'
    description = 'Foursquare Lookup'
    dependencies = {'rho_bot_storage_client', 'rho_bot_rdf_publish', }

    def plugin_init(self):
        self.xmpp.add_event_handler(BotConfiguration.CONFIGURATION_RECEIVED_EVENT, self._configuration_updated)
        self._foursquare_client = None

    def _configuration_updated(self):
        """
        Check to see if the properties for the foursquare service are available, updated, and then create the client
        library to use in this bot.
        :return:
        """
        configuration = self.xmpp['rho_bot_configuration'].get_configuration()

        client_secret = configuration.get(CLIENT_SECRET_KEY, None)
        identifier = configuration.get(IDENTIFIER_KEY, None)

        if client_secret is None or identifier is None:
            self._foursquare_client = None
        else:
            if self._foursquare_client:
                oauth = self._foursquare_client.oauth

                if oauth.client_id == identifier and oauth.client_secret == client_secret:
                    return

            self._foursquare_client = foursquare.Foursquare(client_id=identifier,
                                                            client_secret=client_secret)

    def lookup_foursquare_content(self, node_uri, foursquare_identifier=None):
        """
        Looks up the foursquare details of a venue.
        :param node_uri: the uri of the node to look up.
        :param foursquare_identifier: the identifier of the foursquare data.  If this is not provided, the node will be
        fetched and the first seeAlso property from the node will be used as this parameter.
        :return:
        """

        search_payload = self.xmpp['rho_bot_storage_client'].create_payload()
        search_payload.about = node_uri

        venue = None

        # Attempt to look up the venue id from the details in the node.
        if foursquare_identifier is None:
            result = self.xmpp['rho_bot_storage_client'].get_node(search_payload)
            for see_also in result.properties().get(RDFS.seeAlso, []):
                venue = get_foursquare_venue_from_url(see_also)
                if venue:
                    break
        else:
            venue = get_foursquare_venue_from_url(foursquare_identifier)

        # No point in continuing this exercise if certain requirements are not resolved.
        if not venue:
            logger.error('Cannot find the venue identifier in the node or in parameters.')
            return

        if not self._foursquare_client:
            logger.error('foursquare client is not defined')
            return

        # Finished checking requirements, fetch the details and update.
        venue_details = self._foursquare_client.venues(venue)

        # Translate the venue details into a rdf storage payload for sending to update.
        if 'venue' in venue_details:
            storage_payload = self.xmpp['rho_bot_storage_client'].create_payload()
            foursquare_to_storage(venue_details['venue'], storage_payload)
            storage_payload.about = node_uri

            self.xmpp['rho_bot_storage_client'].update_node(storage_payload)


foursquare_lookup = FoursquareLookup
