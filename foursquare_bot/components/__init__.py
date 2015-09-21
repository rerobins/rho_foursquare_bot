from foursquare_bot.components.knowledge_provider import knowledge_provider
from foursquare_bot.components.foursquare_lookup import foursquare_lookup
from foursquare_bot.components.maintainer import knowledge_maintainer
from foursquare_bot.components.search_handler import search_handler

from sleekxmpp.plugins.base import register_plugin


def load_components():
    """
    Register the core plugins for the system.
    :return: None
    """
    register_plugin(knowledge_provider)
    register_plugin(foursquare_lookup)
    register_plugin(knowledge_maintainer)
    register_plugin(search_handler)
