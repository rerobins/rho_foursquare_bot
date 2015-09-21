"""
Set up the bot for execution.
"""
from rhobot.application import Application
from foursquare_bot.components.commands import load_commands
from foursquare_bot.components import load_components


application = Application()

# Register all of the components that are defined in this application.
application.pre_init(load_commands)
application.pre_init(load_components)

@application.post_init
def register_plugins(bot):
    # Bot Specific Components
    bot.register_plugin('foursquare_lookup')
    bot.register_plugin('knowledge_provider')
    bot.register_plugin('knowledge_maintainer')
    bot.register_plugin('search_handler')

    # Commands
    bot.register_plugin('configure_client_details')
    bot.register_plugin('search_venues')
