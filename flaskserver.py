#!/usr/bin/env python3

import logging
import proverbiosemojies
import everything_formula.everything_formula

import flask
from flask import request
app = flask.Flask(__name__)

def create_logger(name: str, filename: str) -> logging.Logger:
    """Create a logger with name ``name`` that logs to the file ``filename``.

    The logger returned is set to DEBUG level.
    This is based off of the logging cookbook available at
    https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook.
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger_file_handler = logging.FileHandler(filename, encoding = "utf-8")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_file_handler.setFormatter(formatter)
    logger.addHandler(logger_file_handler)
    return logger

# Isto é necessário para correr a app numa path diferente de / (e.g. '/python')
# http://flask.pocoo.org/snippets/35/
class ReverseProxied():
    def __init__(self, app):
        self.app = app
        
    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)
app.wsgi_app = ReverseProxied(app.wsgi_app)

@app.route('/')
def hello():
    return "hello!"

proverb_logger = create_logger("proverbs", "proverbios.log")
@app.route('/proverbiosemojies_webhook', methods = ["POST", "GET"])
def webhook():
    return proverbiosemojies.webhook(proverb_logger)

# as seen in http://mathspp.blogspot.com/2019/04/the-formula-that-plots-itself.html
@app.route('/everything_formula')
def everything_formula_webhook():
    return everything_formula.everything_formula.webhook()


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=8888)