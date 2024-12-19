from flask import Flask
from threading import Thread
import logging
from waitress import serve

app = Flask('')
logging.basicConfig(level=logging.INFO)


@app.route('/')
def home():
    return "I'm alive and running! 🤖"


@app.route('/health')
def health():
    return "OK", 200


def run():
    try:
        serve(app, host='0.0.0.0', port=8080)
    except Exception as e:
        logging.error(f"Error starting web server: {str(e)}")


def keep_alive():
    try:
        t = Thread(target=run)
        t.daemon = True
        t.start()
        logging.info("Production web server started successfully")
    except Exception as e:
        logging.error(f"Error in keep_alive: {str(e)}")
