from rhobot.bot import RhoBot
from rhobot import configuration
import optparse
from foursquare_bot.components import register_components
from foursquare_bot.components.commands import register_commands


register_components()
register_commands()

parser = optparse.OptionParser()
parser.add_option('-c', dest="filename", help="Configuration file for the bot", default='foursquare.rho')
(options, args) = parser.parse_args()

configuration.load_file(options.filename)

bot = RhoBot()
# Bot Specific Components
bot.register_plugin('foursquare_lookup')
bot.register_plugin('knowledge_provider')
bot.register_plugin('knowledge_maintainer')
bot.register_plugin('search_handler')

# Commands
bot.register_plugin('configure_client_details')
bot.register_plugin('search_venues')

# Connect to the XMPP server and start processing XMPP stanzas.
if bot.connect():
    bot.process(block=True)
else:
    print("Unable to connect.")
