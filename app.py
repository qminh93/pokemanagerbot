import requests
import time
import os
import logging
import pickle
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import random

from nltk.chat.eliza import eliza_chatbot
from pogo import util
from pogo.api import PokeAuthSession
from advanced_trainer import Champion

_help = 'Commands List:\n' \
        '/name <your-name> : update your name\n' \
        '/account <gmail-usr> <gmail-pwd> : update your credentials\n' \
        '/do_iv : measure IVs for all pokemons\n' \
        '/do_iv_fast : measure IVs for all recent pokemons\n' \
        '/do_item : manage your inventory\n' \
        '/do_poke : manage your party\n' \
        '/verbose : print operation details\n' \
        '/silence : suppress operation details\n' \
        '/want <pokemon-name> : indicate that you want to catch this pokemon\n' \
        '/unwant <pokemon-name> : indicate that catching this pokemon is no longer your priority'

class Preference:
    def __init__(self, name = 'Anonymous', usr = 'None', pwd = 'None', loc = None, verbose = False):
        self.name = name
        self.usr = usr
        self.pwd = pwd
        self.verbose = verbose
        self.loc = loc
        self.wanted = set()

    def credentials(self):
        return [self.usr, self.pwd]

def reverse_geocode(latitude, longitude):
    # grab some lat/long coords from wherever. For this example,
    # I just opened a javascript console in the browser and ran:
    #
    # navigator.geolocation.getCurrentPosition(function(p) {
    #   console.log(p);
    # })
    #

    # Did the geocoding request comes from a device with a
    # location sensor? Must be either true or false.
    sensor = 'true'

    # Hit Google's reverse geocoder directly
    # NOTE: I *think* their terms state that you're supposed to
    # use google maps if you use their api for anything.
    base = "http://maps.googleapis.com/maps/api/geocode/json?"
    params = "latlng={lat},{lon}&sensor={sen}".format(
        lat=latitude,
        lon=longitude,
        sen=sensor
    )
    url = "{base}{params}".format(base=base, params=params)
    response = requests.get(url)
    return response.json()['results'][0]['formatted_address']

def load(db):
    users = dict()
    if os.path.isfile(db):
        with open(db, "rb") as f:
            users = pickle.load(f)
    return users

def save(db, users):
    with open(db, "wb") as f:
        pickle.dump(users, f)

def invalid_command(chat_id):
    bot.sendMessage(chat_id, 'Invalid command. Please refer to the following list of supported commands: /do_item: manage your items; /do_poke: manage your pokemons; /do_iv: compute ivs for your pokemons')

def process_command(chat_id):
    bot.sendMessage(chat_id,'Dear %s,\nYour command is being processed. Please refrain from logging into Pokemon Go and wait for my confirmation.' %users[chat_id].name)

def finish_command(chat_id):
    bot.sendMessage(chat_id, 'Your command has been processed. You can now log in to check.')

def send_help(chat_id):
    bot.sendMessage(chat_id, _help)

def new_users(chat_id):
    users[chat_id] = Preference()
    bot.sendMessage(chat_id, 'Hello! My name is Prof. Papyrus. I am your new Pokemon Go Assistant.')
    bot.sendMessage(chat_id, 'Seems like i do not know you. What is your name (/name <your-name>) ?')

def greet_users(chat_id):
    if chat_id not in users: new_users(chat_id)
    else: bot.sendMessage(chat_id, 'Hello %s. How may I help you ?' % users[chat_id].name)

def talk_to_users(chat_id):
    if chat_id not in users: new_users(chat_id)
    bot.sendMessage(chat_id, 'Hey %s ! Talk to me. You are boring as fuck !' % users[chat_id].name)

def want_pokemon(chat_id, pokename):
    if pokename not in users[chat_id].wanted: users[chat_id].wanted.add(pokename)
    if lax == 0: save(db, users)
    bot.sendMessage(chat_id, pokename + ' has been added to your wanted list.')

def unwant_pokemon(chat_id, pokename):
    users[chat_id].wanted.discard(pokename)
    if lax == 0: save(db, users)
    bot.sendMessage(chat_id, pokename + ' has been removed from your wanted list.')

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if content_type == 'location':
        if chat_id not in users: new_users(chat_id)
        users[chat_id].loc = msg['location']
        if lax == 0: save(db, users)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Spin Nearby Pokestops', callback_data='spin')],
            [InlineKeyboardButton(text='Catch Nearby Pokemons', callback_data='catch')],
            [InlineKeyboardButton(text='Walk Around And Catch', callback_data='walk')],
            [InlineKeyboardButton(text='Bot', callback_data='bot')]
        ]#, resize_keyboard=True, one_time_keyboard=True
        )
        bot.sendMessage(chat_id, 'Scanning surrounding ...', reply_markup=keyboard)
    elif content_type == 'text':
        message = msg['text']
        tokens = message.split()
        command = tokens[0]
        if command.startswith('/'):
            if command == '/start': greet_users(chat_id)
            else:
                if chat_id not in users: new_users(chat_id)
                if command == '/name':
                    if (len(tokens) < 2):
                        bot.sendMessage(chat_id, 'Sorry. What is your name again ?')
                    else:
                        name = ' '.join(tokens[1:])
                        users[chat_id].name = name
                        bot.sendMessage(chat_id, 'Nice to meet you, %s' % name)
                        if lax == 0: save(db, users)
                elif command == '/account':
                    if len(tokens) < 3:
                        bot.sendMessage(chat_id, ' '.join(users[chat_id].credentials()))
                    else:
                        users[chat_id].usr = tokens[1]
                        users[chat_id].pwd = tokens[2]
                        bot.sendMessage(chat_id, 'Your credentials have been updated successfully.')
                        if lax == 0: save(db, users)
                elif command == '/help':
                    send_help(chat_id)
                elif command == '/verbose':
                    users[chat_id].verbose = True
                    bot.sendMessage(chat_id, 'Sure. You will be updated with more managing details.')
                    if lax == 0: save(db, users)
                elif command == '/silence':
                    users[chat_id].verbose = False
                    bot.sendMessage(chat_id, 'Sure. You will be updated with less managing details.')
                    if lax == 0: save(db, users)
                elif command.startswith('/want'):
                    if len(tokens) < 2: invalid_command(chat_id)
                    else: want_pokemon(chat_id, tokens[1])
                elif command.startswith('/unwant'):
                    if len(tokens) < 2: invalid_command(chat_id)
                    else: unwant_pokemon(chat_id, tokens[1])
                elif command.startswith('/do'):
                    [usr, pwd] = users[chat_id].credentials()
                    auth_session = PokeAuthSession(usr, pwd, 'google', './encrypt.so', geo_key = None)
                    session = auth_session.authenticate()
                    if session:
                        trainer = Champion(auth_session, session)
                        trainer.getProfile()
                        trainer.checkInventory()
                        time.sleep(1)
                        process_command(chat_id)
                        valid_command = True

                        if command == '/do_item':
                            trainer.manage_items(100, 50, 50, 200, verbose = users[chat_id].verbose)
                        elif command == '/do_poke':
                            trainer.manage_pokemon(bot, chat_id, verbose = users[chat_id].verbose)
                        elif command == '/do_iv':
                            trainer.measure_pokemon(bot, chat_id, verbose = users[chat_id].verbose)
                        elif command == '/do_iv_fast':
                            trainer.measure_pokemon(bot, chat_id, recent = True, verbose = users[chat_id].verbose)
                        else:
                            valid_command = False
                            invalid_command(chat_id)

                        if valid_command: finish_command(chat_id)
                    else: bot.sendMessage(chat_id, 'Please update your credentials using /account <usr> <pwd>')
                elif command == '/scan':
                    markup = ReplyKeyboardMarkup(keyboard = [
                        [KeyboardButton(text = 'Send Location', request_location = True)]
                    ], resize_keyboard = True, one_time_keyboard = True
                    )
                    bot.sendMessage(chat_id, 'Scanning surroundings ...', reply_markup = markup)
                else: invalid_command(chat_id)
        else: bot.sendMessage(chat_id, eliza_chatbot.respond(message))

def loc2str(lat, lon):
    return str(lat) + ',' + str(lon)

def spin(chat_id, trainer, session, verbose):
    logging.info('Spinning nearby Pokemon Stops')
    bot.sendMessage(chat_id, 'OK. I am going to spin nearby Pokemon Stops for you. Please wait here until I come back.')
    stops = trainer.sortCloseForts()
    if len(stops) > 0:
        for i, stop in enumerate(stops):
            if verbose: bot.sendMessage(chat_id, 'Visiting ' + session.getFortDetails(stop).name)
            if i == 5: break
            trainer.WalkAndSpin(bot, chat_id, stop, users[chat_id].verbose)
        if verbose: bot.sendMessage(chat_id, 'I am running back to your location now.')
        trainer.walkTo(users[chat_id].loc['latitude'], users[chat_id].loc['longitude'], step = 9.0)
        bot.sendMessage(chat_id, 'Hi %s, I am back.' % users[chat_id].name)
    else:
        logging.info('There is no nearby Pokemon Stop')
        bot.sendMessage(chat_id, 'Unfortunately, there is no nearby Pokemon Stop. I will stay here with you.')

def catch(chat_id, trainer, session, verbose):
    logging.info('Catching nearby pokemons')
    bot.sendMessage(chat_id, 'OK. I will try to catch some nearby pokemons for you. Please wait here until I come back.')
    time.sleep(5)
    pokemons = trainer.FindAllPokemons(bot, chat_id)
    if len(pokemons) > 0:
        for i, poke in enumerate(pokemons):
            if i == 5: break
            trainer.catchPokemon(poke, bot, chat_id, users[chat_id].verbose)
            time.sleep(7)
        if verbose: bot.sendMessage(chat_id, 'I am running back to your location now. Please wait for me.')
        trainer.walkTo(users[chat_id].loc['latitude'], users[chat_id].loc['longitude'], step = 9.0)
        bot.sendMessage(chat_id, 'Hi %s, I am back.' % users[chat_id].name)
    elif verbose:
        logging.info('There is no nearby pokemon')
        bot.sendMessage(chat_id, 'Unfortunately, I see no nearby pokemon. I will stay here with you.')

def walk(chat_id, trainer, session, verbose):
    logging.info('Walking around to catch pokemons')
    bot.sendMessage(chat_id, 'OK. I will go around to catch some pokemons for you. Please wait here until I come back.')
    lat_shift = users[chat_id].loc['latitude']
    lon_shift = users[chat_id].loc['longitude']

    encountered = []

    for i in range(10):
        poke = trainer.FindBestPokemon(bot, chat_id, users[chat_id].wanted)
        encounterId = None
        if poke: encounterId = getattr(poke, "encounter_id", None)
        if poke and encounterId not in encountered:
            trainer.catchPokemon(poke, bot, chat_id, verbose)
            trainer.walkTo(lat_shift, lon_shift, step = 3.2)
        elif verbose: bot.sendMessage(chat_id, 'Unfortunately, I see no nearby pokemon.')
        lat_shift += float(random.randint(-30, 30)) / 10000.0
        lon_shift += float(random.randint(-30, 30)) / 10000.0
        if verbose: bot.sendMessage(chat_id, 'I will walk out a bit further.')
        trainer.walkTo(lat_shift, lon_shift, step = 3.2)
        time.sleep(10)

    bot.sendMessage(chat_id, 'It has been a while. I am coming back to you now.')
    trainer.walkTo(users[chat_id].loc['latitude'], users[chat_id].loc['longitude'], step = 9.0)
    bot.sendMessage(chat_id, 'Hi %s, I am back.' % users[chat_id].name)

def on_callback_query(msg):

    query_id, chat_id, query_data = telepot.glance(msg, flavor = 'callback_query')
    bot.answerCallbackQuery(query_id, text = 'I am on my way.')

    if query_data == 'spin' or query_data == 'catch' or query_data == 'walk' or query_data == 'bot':
        [usr, pwd] = users[chat_id].credentials()
        loc = loc2str(users[chat_id].loc['latitude'],users[chat_id].loc['longitude'])
        auth_session = PokeAuthSession(usr, pwd, 'google', './encrypt.so', geo_key=None)
        session = auth_session.authenticate(locationLookup = loc)
        if session:
            trainer = Champion(auth_session, session)
            trainer.getProfile()
            trainer.checkInventory()
            time.sleep(1)
            process_command(chat_id)
            is_valid = True
            if query_data == 'spin': spin(chat_id, trainer, session, users[chat_id].verbose)
            elif query_data == 'catch': catch(chat_id, trainer, session, users[chat_id].verbose)
            elif query_data == 'walk': walk(chat_id, trainer, session, users[chat_id].verbose)
            elif query_data == 'bot': trainer.advanceBot(bot, chat_id, session, users[chat_id].wanted, users[chat_id].verbose)
            else:
                is_valid = False
                invalid_command(chat_id)
            if is_valid: finish_command(chat_id)


TOKEN = '283747572:AAEdfrOnYTglaSYAqx4g0kBPHlBV7IoEifw'  # get token from command-line

bot = telepot.Bot(TOKEN)
bot.message_loop({'chat': on_chat_message,
                  'callback_query': on_callback_query})

util.setupLogger()
logging.debug('Logger set up')
print('Listening ...')
db = "DB.dat"
users = load(db)


count = 0
period = 50
lax = 0
talk = 300

'''
for pokemonId in range(151):
    urllib.urlretrieve("https://silphroad-s3-xika4hn.netdna-ssl.com/img/pokemon/icons/96x96/" + str(pokemonId + 1) + '.png', './icons/' + str(pokemonId + 1) + '.png')
    Image.open('./icons/' + str(pokemonId + 1) + '.png').convert('RGB').save('./icons/' + str(pokemonId + 1) + '.jpg')
'''

#print('Number of current users is %i.' % len(users))

while 1:
    time.sleep(10)
    count += 1
    if lax == 1 and count % period == 0: save(db, users)
    if count % talk == 0:
       idx = random.randint(0, len(users) - 1)
       keys = list(users)
       chat_id = keys[idx]
       print(users[chat_id].name)
       talk_to_users(chat_id)

'''
bot = telepot.aio.Bot(TOKEN)
loop = asyncio.get_event_loop()

util.setupLogger()
logging.debug('Logger set up')

loop.create_task(bot.message_loop(on_chat_message))

db = "DB.dat"
users = load(db)
lax = 0
print('Listening ...')

loop.run_forever()
'''