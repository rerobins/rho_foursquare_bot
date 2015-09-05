"""
This is a module that will attempt to populate the empty foursquare details
"""
from sleekxmpp.plugins.base import base_plugin
from rhobot.components.configuration import BotConfiguration
from foursquare_bot.components.namespace import WGS_84, SCHEMA
from rhobot.components.storage import StoragePayload
from rhobot.components.storage.namespace import NEO4J
from rdflib.namespace import RDFS
import logging


logger = logging.getLogger(__name__)


class KnowledgeMaintainer(base_plugin):
    name = 'knowledge_maintainer'
    description = 'Knowledge Maintainer'
    dependencies = {'rho_bot_storage_client', 'rho_bot_rdf_publish', 'rho_bot_scheduler', 'foursquare_lookup', }

    work_to_do_delay = 1.0
    no_work_delay = 600.0

    def plugin_init(self):
        """
        Start the process when the configuration is updated.
        :return:
        """
        self.xmpp.add_event_handler(BotConfiguration.CONFIGURATION_RECEIVED_EVENT, self._configuration_updated)

    def _configuration_updated(self, event):
        """
        Kick off the work to do task.
        :param event:
        :return:
        """
        self.xmpp['rho_bot_scheduler'].schedule_task(self._start_process, delay=self.work_to_do_delay)
        self.xmpp.del_event_handler(BotConfiguration.CONFIGURATION_RECEIVED_EVENT, self._configuration_updated)

    def _start_process(self):
        """
        Start the process of updating unpopulated foursquare references.
        :return:
        """
        promise = self.xmpp['rho_bot_scheduler'].defer(self._create_session)
        promise = promise.then(self._find_work_node)
        promise = promise.then(self._work_node)

        # If the promise has been resolved, then should check to see if there are new values to populate using the
        # work_to_do_delay, otherwise use the no_work_delay
        promise.then(self._schedule_work_to_do, self._schedule_no_work_task)

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
        query = """MATCH (n:`%s`)
                   WHERE any(seealso IN n.`%s` WHERE seealso =~ '^foursquare:.*')
                   and not(has(n.`%s`)) RETURN n as node LIMIT 1""" % (str(WGS_84.SpatialThing),
                                                                       str(RDFS.seeAlso),
                                                                       str(SCHEMA.name))

        logger.debug('Executing query: %s' % query)

        payload = StoragePayload()
        payload.add_property(key=NEO4J.cypher, value=query)
        result = self.xmpp['rho_bot_storage_client'].execute_cypher(payload)

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

        promise = self.xmpp['foursquare_lookup'].schedule_lookup(node_uri).then(lambda s: session)

        return promise

    def _schedule_work_to_do(self, session):
        logger.info('Scheduling cause there is still work to do.')
        self.xmpp['rho_bot_scheduler'].schedule_task(self._start_process, delay=self.work_to_do_delay)

    def _schedule_no_work_task(self, session):
        logger.info('Scheduling later cause there is NO work to do')
        self.xmpp['rho_bot_scheduler'].schedule_task(self._start_process, delay=self.no_work_delay)


knowledge_maintainer = KnowledgeMaintainer
