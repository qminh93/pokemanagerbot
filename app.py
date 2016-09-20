import time
#import logging
import telepot

#from pogo import util
from pogo.api import PokeAuthSession
from advanced_trainer import Champion

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == 'text':
        command = msg['text']
        if command.startswith('/'):
            if command == '/start':
                bot.sendMessage(chat_id, 'Hello. I am your Pokemon Go Manager')
            elif command == '/end':
                bot.sendMessage(chat_id, 'Bye')
            elif command.startswith('/manage'):
                tokens = command.split()
                if len(tokens) < 3:
                    bot.sendMessage(chat_id, 'Not enough arguments')
                else:
                    usr = tokens[1]
                    pwd = tokens[2]
                    auth_session = PokeAuthSession(usr, pwd, 'google', './encrypt.so', geo_key = None)
                    session = auth_session.authenticate()

                    if session:
                        trainer = Champion(auth_session, session)
                        trainer.getProfile()
                        trainer.checkInventory()
                        time.sleep(1)
                        if tokens[0] == '/manage_items':
                            trainer.manage_items(100, 50, 50, 200)
                            bot.sendMessage(chat_id, 'Done.')
                        elif tokens[0] == '/manage_pokemons':
                            released_log = trainer.manage_pokemon()
                            bot.sendMessage(chat_id,'Done.')
                            for pokemon in released_log: bot.sendMessage(chat_id, pokemon)
                        elif tokens[0] == '/manage_iv':
                            trainer.measure_pokemon()
                            bot.sendMessage(chat_id,'Done')
                        else:
                            bot.sendMessage(chat_id,'Invalid command.')
            else:
                bot.sendMessage(chat_id,'Invalid command.')


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    bot.answerCallbackQuery(query_id, text='Got it')

TOKEN = '283747572:AAEdfrOnYTglaSYAqx4g0kBPHlBV7IoEifw'  # get token from command-line

bot = telepot.Bot(TOKEN)
bot.message_loop({'chat': on_chat_message,
                  'callback_query': on_callback_query})

#util.setupLogger()
#logging.debug('Logger set up')
print('Listening ...')

while 1:
    time.sleep(10)
