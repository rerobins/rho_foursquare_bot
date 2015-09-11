from sleekxmpp.plugins.base import base_plugin
from rhobot.components.configuration import BotConfiguration
from rhobot.components.storage import StoragePayload
from foursquare_bot.components.configuration_enums import CLIENT_SECRET_KEY, IDENTIFIER_KEY
from foursquare_bot.components.utilities import get_foursquare_venue_from_url, foursquare_to_storage
import logging
import foursquare
from rdflib.namespace import RDFS, DCTERMS

logger = logging.getLogger(__name__)


class FoursquareLookup(base_plugin):
    name = 'foursquare_lookup'
    description = 'Foursquare Lookup'
    dependencies = {'rho_bot_storage_client', 'rho_bot_rdf_publish', 'rho_bot_representation_manager', }

    def plugin_init(self):
        self.xmpp.add_event_handler(BotConfiguration.CONFIGURATION_RECEIVED_EVENT, self._configuration_updated)
        self._foursquare_client = None

    def post_init(self):
        self._configuration = self.xmpp['rho_bot_configuration']
        self._storage_client = self.xmpp['rho_bot_storage_client']
        self._rdf_publish = self.xmpp['rho_bot_rdf_publish']
        self._scheduler = self.xmpp['rho_bot_scheduler']
        self._representation_manager = self.xmpp['rho_bot_representation_manager']

    def _configuration_updated(self, event):
        """
        Check to see if the properties for the foursquare service are available, updated, and then create the client
        library to use in this bot.
        :return:
        """
        configuration = self._configuration.get_configuration()

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
        def update_venue_details(venue):
            # No point in continuing this exercise if certain requirements are not resolved.
            if not venue:
                raise RuntimeError('Venue identifier is not defined')

            if not self._foursquare_client:
                raise RuntimeError('Foursquare client is not defined')

            # Finished checking requirements, fetch the details and update.
            logger.debug('Looking up venue: %s' % venue)
            venue_details = self._foursquare_client.venues(venue)

            # Translate the venue details into a rdf storage payload for sending to update.
            if 'venue' in venue_details:
                storage_payload = StoragePayload()
                foursquare_to_storage(venue_details['venue'], storage_payload)
                storage_payload.about = node_uri
                storage_payload.add_reference(DCTERMS.creator, self._representation_manager.representation_uri)

                return self._storage_client.update_node(storage_payload)

        # Attempt to look up the venue id from the details in the node.
        if foursquare_identifier is None:
            search_payload = StoragePayload()
            search_payload.about = node_uri
            promise = self._storage_client.get_node(search_payload).then(self._handle_get_node)
        else:
            promise = self._scheduler.promise()
            venue_identifier = get_foursquare_venue_from_url(foursquare_identifier)
            promise.resolved(venue_identifier)

        promise = promise.then(update_venue_details)

        return promise

    def _handle_get_node(self, result):
        venue = None
        for see_also in result.properties.get(str(RDFS.seeAlso), []):
            venue = get_foursquare_venue_from_url(see_also)
            if venue:
                break
        return venue

    def schedule_lookup(self, node_uri, foursquare_identifier=None, create=False):
        """
        Schedule a lookup on the node to be executed later.
        :param node_uri: uri to look up.
        :return:
        """

        promise = self._scheduler.defer(self.lookup_foursquare_content, node_uri, foursquare_identifier)

        if create:
            return promise.then(self._publish_create)
        else:
            return promise.then(self._publish_update)

    def _publish_update(self, result):
        """
        Publish the update information to the channel.
        :param result: result collection
        :return:
        """
        self._rdf_publish.publish_all_results(result, created=False)

    def _publish_create(self, result):
        """
        Publish the update information to the channel.
        :param result: result collection
        :return:
        """
        self._rdf_publish.publish_all_results(result, created=True)

    def search_foursquare(self, near, query=None):
        """
        Search foursquare.
        :param near: near a location
        :param query: query to search for.
        :return: list of id, name dictionaries.
        """
        parameters = dict(near=near, limit=10)
        if query:
            parameters['query'] = query

        venue_results = self._foursquare_client.venues.search(parameters)

        logger.debug('venue_results: %s' % venue_results['venues'])

        return venue_results['venues']


foursquare_lookup = FoursquareLookup
