#!/usr/bin/env python3

import proverbsemojies
#import everything_formula.everything_formula

import flask
from flask import request
app = flask.Flask(__name__)

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

@app.route('/proverbsemojies_webhook', methods = ["POST", "GET"])
def webhook():
    return proverbsemojies.webhook()

"""
# as seen in http://mathspp.blogspot.com/2019/04/the-formula-that-plots-itself.html
@app.route('/everything_formula')
def everything_formula_webhook():
    return everything_formula.everything_formula.webhook()
"""

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=8888)