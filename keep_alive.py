from flask import Flask, make_response
from threading import Thread
import logging
from waitress import serve
from functools import wraps

app = Flask('')
logging.basicConfig(level=logging.INFO)

def cache_response(timeout=5 * 60):  # 5 minute cache
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            response = make_response(f(*args, **kwargs))
            response.cache_control.max_age = timeout
            response.cache_control.public = True
            return response
        return wrapper
    return decorator

@app.route('/')
@cache_response(timeout=5 * 60)
def home():
    return "I'm alive and running! 🤖"

@app.route('/health')
@cache_response(timeout=60)  # 1 minute cache for health checks
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
