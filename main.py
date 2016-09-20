import os
from flask import Flask, request
import telepot

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

app = Flask(__name__)
TOKEN = os.environ['PP_BOT_TOKEN']  # put your token in heroku app as environment variable
SECRET = '/bot' + TOKEN
URL = 'https://pokemanagerbot.herokuapp.com/' #  paste the url of your application

UPDATE_QUEUE = Queue()
BOT = telepot.Bot(TOKEN)

def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    BOT.sendMessage(chat_id, 'hello!')

BOT.message_loop({'chat': on_chat_message}, source=UPDATE_QUEUE)  # take updates from queue

@app.route(SECRET, methods=['GET', 'POST'])
def pass_update():
    UPDATE_QUEUE.put(request.data)  # pass update to bot
    return 'OK'

BOT.setWebhook() # unset if was set previously
BOT.setWebhook(URL + SECRET)
