from foursquare_bot.components.commands.configure_client_details import configure_client_details
from foursquare_bot.components.commands.search_venues import search_venues

from sleekxmpp.plugins.base import register_plugin


def register_commands():
    """
    Register the core plugins for the system.
    :return: None
    """
    register_plugin(configure_client_details)
    register_plugin(search_venues)
