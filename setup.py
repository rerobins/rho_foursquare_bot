from distutils.core import setup

setup(
    name='foursquare_bot',
    version='1.0.0',
    packages=['foursquare_bot',
              'foursquare_bot.components',
              'foursquare_bot.components.commands',
              'foursquare_bot.components.events',
              ],
    url='',
    license='BSD',
    author='Robert Robinson',
    author_email='rerobins@meerkatlabs.org',
    description='Foursuqare connection bot for the Rho infrastructure',
    install_requires=['rhobot==1.0.0', 'foursquare==20130707', ]
)
