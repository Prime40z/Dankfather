from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    """Creates and starts new thread that runs the flask server."""
    t = Thread(target=run)
    t.start()
