"""
This is a module that will attempt to populate the empty foursquare details
"""
from sleekxmpp.plugins.base import base_plugin
from rhobot.components.configuration import BotConfiguration
from rhobot.namespace import WGS_84, SCHEMA
from rhobot.components.storage import StoragePayload
from rhobot.components.storage.namespace import NEO4J
from rdflib.namespace import RDFS
import logging


logger = logging.getLogger(__name__)


class KnowledgeMaintainer(base_plugin):
    name = 'knowledge_maintainer'
    description = 'Knowledge Maintainer'
    dependencies = {'rho_bot_storage_client',
                    'rho_bot_rdf_publish',
                    'rho_bot_scheduler',
                    'foursquare_lookup', }

    work_to_do_delay = 1.0
    no_work_delay = 600.0

    query = """MATCH (n:`%s`)
                   WHERE any(seealso IN n.`%s` WHERE seealso =~ '^foursquare:.*')
                   and not(has(n.`%s`)) RETURN n as node LIMIT 1""" % (str(WGS_84.SpatialThing),
                                                                       str(RDFS.seeAlso),
                                                                       str(SCHEMA.name))

    def plugin_init(self):
        """
        Start the process when the configuration is updated.
        :return:
        """
        self.xmpp.add_event_handler(BotConfiguration.CONFIGURATION_RECEIVED_EVENT, self._configuration_updated)
        self.query = ' '.join(self.query.replace('\n', ' ').replace('\r', '').split())

    def post_init(self):
        super(KnowledgeMaintainer, self).post_init()

        self._storage_client = self.xmpp['rho_bot_storage_client']
        self._rdf_publish = self.xmpp['rho_bot_rdf_publish']
        self._scheduler = self.xmpp['rho_bot_scheduler']
        self._foursquare_lookup = self.xmpp['foursquare_lookup']

    def _configuration_updated(self, event):
        """
        Kick off the work to do task.
        :param event:
        :return:
        """
        self._scheduler.schedule_task(self._start_process, delay=self.work_to_do_delay)

        # After the configuration has been received, remove the listener so that the process isn't started each time.
        self.xmpp.del_event_handler(BotConfiguration.CONFIGURATION_RECEIVED_EVENT, self._configuration_updated)

    def _start_process(self):
        """
        Start the process of updating unpopulated foursquare references.
        :return:
        """
        promise = self._scheduler.defer(self._create_session)
        promise = promise.then(self._find_work_node)
        promise = promise.then(self._work_node)

        # If the promise has been resolved, then should check to see if there are new values to populate using the
        # work_to_do_delay, otherwise use the no_work_delay
        promise.then(self._scheduler.generate_promise_handler(self._reschedule, self.work_to_do_delay),
                     self._scheduler.generate_promise_handler(self._reschedule, self.no_work_delay))

    def _create_session(self):
        """
        Create a session variable for the work load that is being done.
        :return:
        """
        return dict()

    def _find_work_node(self, session):
        """
        Find node to do work over.
        :return:
        """
        logger.debug('Executing query: %s' % self.query)

        payload = StoragePayload()
        payload.add_property(key=NEO4J.cypher, value=self.query)
        promise = self._storage_client.execute_cypher(payload).then(
            self._scheduler.generate_promise_handler(self._handle_results, session))

        return promise

    def _handle_results(self, result, session):

        if not result.results:
            raise Exception('No results to work')

        node_uri = result.results[0].about

        session['node'] = node_uri

        return session

    def _work_node(self, session):
        """
        Do the work on the node to populate the details.
        :param session: session variable containing previous step details.
        :return: session
        """
        node_uri = session.get('node', None)
        if not node_uri:
            raise Exception('No node defined')

        # Schedule the look up, and then return the session variable so that further work can be done.
        promise = self._foursquare_lookup.schedule_lookup(node_uri).then(lambda s: session)

        return promise

    def _reschedule(self, session, delay=300.0):
        """
        Reschedule the task after a specified delay time.
        :param session:
        :param delay:
        :return:
        """
        logger.debug('Reschedule the lookup in %s seconds' % delay)
        self._scheduler.schedule_task(self._start_process, delay=delay)


knowledge_maintainer = KnowledgeMaintainer
