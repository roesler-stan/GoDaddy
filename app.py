#!/usr/bin/env python

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on available packages.
async_mode = None
ping_interval = 5
ping_timeout = 15

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)

# monkey patching is necessary because this application uses a background thread
if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()

from flask import Flask, render_template, request, redirect, Response, flash
# from flask.ext.socketio import SocketIO, emit
from flask.ext.sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from threading import Thread
from constants import *
from tasks import *
import clean_input
import os
import datetime
import time
import pandas

app = Flask(__name__)
app.secret_key = 'Katharina made this.'
socketio = SocketIO(app, async_mode = async_mode)
thread = None

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "postgres://localhost")
db = SQLAlchemy(app)

# at every reload, reset the thread in case the user hit back and wants to perform a new search
# global thread
# thread = None
# print 'reseting thread at index page'

@app.route('/')
def frontpage():
    return redirect('/index')

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/queue', methods = ['POST'])
def queue():
    # Reset the thread in case the user hit back and wants to perform a new search
    global thread
    thread = None

    error = ''
    search_page = request.form['form_type']

    if search_page == 'list':
        domains_list = request.form['domains_list']
        extensions = request.form.getlist('extensions')
        domain_names, domain_errors = clean_input.generate_list_domains(domains_list, extensions)

        # if len(domain_names) >= 200:
        #     domain_errors.append('Please choose fewer than 200 domain names.')
        error += '\n'.join(domain_errors)
        if error:
            return render_template('list.html', error = error)
    
    elif search_page == 'keywords':
        keywords_allcombos = request.form['keywords_allcombos']
        keywords1 = request.form['keywords1']
        keywords2 = request.form['keywords2']
        keywords_unordered = request.form.get('keywords_unordered')
        extensions = request.form.getlist('extensions')

        if not extensions:
            error = 'Please choose at least one extension.'
            return render_template('keywords.html', error = error)

        domain_names, domain_errors = clean_input.generate_keyword_domains(keywords_allcombos, keywords1, keywords2, keywords_unordered, extensions)

        # if len(domain_names) >= 200:
        #     domain_errors.append('Please choose fewer than 200 domain names.')
        error += '\n'.join(domain_errors)
        if error:
            return render_template('keywords.html', error = error)

    time_requested = datetime.datetime.utcnow()
    ip_address = request.remote_addr
    result_id = ip_address + ' requested at time ' + str(time_requested)

    resp = find_domains.delay(domain_names, result_id)
    request_id = resp.id
    
    user = Users(result_id, request_id, time_requested, ip_address)
    db.session.add(user)
    db.session.commit()
    
    return redirect('/results/' + request_id)

def check_result(request_id):
    """ Check for result and send 'results ready' to processing page if it is ready. """
    while True:
        result = AsyncResult(request_id)
        if result.ready() and result.successful():
            socketio.emit('my response', {'data': 'results ready'}, namespace = '/test')
            break
        else:
            socketio.emit('my response', {'data': 'not ready'}, namespace = '/test')
        time.sleep(5)
        print 'still in thread'

@app.route('/results/<request_id>')
def results(request_id):
    global thread
    if thread is None:
        print 'no thread found, so starting one'
        thread = Thread(target = check_result, args = (request_id,))
        thread.daemon = True
        thread.start()

    result = AsyncResult(request_id)
    if result.ready() and result.successful():
        return render_template('results.html', table_data = result.get())
    elif result.failed():
        return result.traceback
    # if there's a socket timeout or some other failure
        # return render_template('failure.html')
    else:
        return render_template('processing.html')

@socketio.on('my response', namespace = '/test')
def test_message(message):
    emit('my response', {'data': message['data']})

# @app.route('/results_example')
# def results_example():
#     return render_template('results_example.html')

@app.route('/list')
def list():
    return render_template('list.html')

@app.route('/keywords')
def keywords():
    return render_template('keywords.html')

class Users(db.Model):
    result_id = db.Column(db.String(200), primary_key = True)
    request_id = db.Column(db.String(120))
    time_requested = db.Column(db.DateTime, default = datetime.datetime.utcnow)
    ip_address = db.Column(db.String(120))

    def __init__(self, result_id, request_id, time_requested, ip_address):
        self.result_id = result_id
        self.request_id = request_id
        self.time_requested = time_requested
        self.ip_address = ip_address

    def __repr__(self):
        return '<Request ID %r with result id at %r>' % self.request_id % self.result_id

class Result(db.Model):
    result_id = db.Column(db.String(200), primary_key = True)
    domain = db.Column(db.String(100), primary_key = True)
    available = db.Column(db.String(10))
    price_year1 = db.Column(db.String(20))
    price_renewal = db.Column(db.String(20))
    price_min_offer = db.Column(db.String(20))
    price_buy_now = db.Column(db.String(20))
    godaddy_link = db.Column(db.String(200))

    def __init__(self, result_id, domain, available, price_year1, price_renewal, price_min_offer, price_buy_now, godaddy_link):
        self.result_id = result_id
        self.domain = domain
        self.available = available
        self.price_year1 = price_year1
        self.price_renewal = price_renewal
        self.price_min_offer = price_min_offer
        self.price_buy_now = price_buy_now
        self.godaddy_link = godaddy_link

if __name__ == "__main__":
    socketio.run(app, debug = True)
    # app.run(debug = True)