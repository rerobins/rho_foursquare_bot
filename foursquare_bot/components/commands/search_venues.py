"""
This command will be used to search the foursquare venue database for locations that can be added to the database.
"""

from rhobot.components.commands.base_command import BaseCommand
import logging

logger = logging.getLogger(__name__)

class SearchVenues(BaseCommand):

    def initialize_command(self):
        super(SearchVenues, self).initialize_command()

        logger.info('Initialize Command')
        self._initialize_command(identifier='search_venues', name='Search Venues',
                                 additional_dependencies={'foursquare_lookup'})

    def command_start(self, request, initial_session):
        """
        Provide the configuration details back to the requester and end the command.
        :param request:
        :param initial_session:
        :return:
        """
        form = self.xmpp['xep_0004'].make_form()

        form.add_field(var='near', label='Near', ftype='text-single', description='Search City')
        form.add_field(var='query', label='Query', ftype='text-single', description='Query String')

        initial_session['payload'] = form
        initial_session['next'] = self.perform_search
        initial_session['has_next'] = True

        return initial_session

    def perform_search(self, payload, session):
        """
        With the provided information, search the foursquare database.
        :param payload:
        :param session:
        :return:
        """
        form = payload
        near = form.get_fields()['near'].get_value()
        query = form.get_fields()['query'].get_value()

        # Search the foursquare database for the contents.
        results = self.xmpp['foursquare_lookup'].search_foursquare(near=near, query=query)

        session['venues'] = {}
        options = []
        for result in results:
            name = result['name']
            location_id = result['id']

            session['venues'][location_id] = result

            if 'location' in result:
                if 'address' in result['location']:
                    name += ' (%s)' % result['location']['address']

            options.append(dict(value=location_id, label=name))

        new_form = self.xmpp['xep_0004'].make_form()
        new_form.add_field(var='location', label='Select Location', options=options, type='list-single')

        session['payload'] = new_form
        session['next'] = self.select_item
        session['has_next'] = False

        return session

    def select_item(self, payload, session):
        """
        Process the selected item by:
        place in the node database
        schedule a look up of the details.
        return the value and label of the location so that it can be used in any parent commands.
        :param payload:
        :param session:
        :return:
        """

        logger.debug('Received payload: %s' % payload)

        form = self.xmpp['xep_0004'].make_form(ftype='result')

        form.add_reported(var='value', ftype='text-single')
        form.add_reported(var='label', ftype='text-single')

        location_id = payload.get_fields()['location'].get_value()

        form.add_item({'value': location_id,
                       'label': session['venues'][location_id]['name']})

        session['has_next'] = False
        session['payload'] = form
        session['next'] = None

        return session

search_venues = SearchVenues
