import time
import telepot

"""
$ python2.7 skeleton.py <token>
A skeleton for your telepot programs.
"""

def handle(msg):
    flavor = telepot.flavor(msg)

    summary = telepot.glance(msg, flavor=flavor)
    print flavor, summary


TOKEN = '283747572:AAEdfrOnYTglaSYAqx4g0kBPHlBV7IoEifw'

bot = telepot.Bot(TOKEN)
bot.message_loop(handle)
print 'Listening ...'

# Keep the program running.
while 1:
    time.sleep(10)