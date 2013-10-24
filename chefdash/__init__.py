import gevent
import gevent.monkey
import gevent.socket
gevent.monkey.patch_all()

import subprocess
import fcntl
import os
import errno
import sys
import urllib

import gevent.queue
import gevent.event
import ujson

import flask
import flask.ext.login

import chef

import logging

app = flask.Flask('chefdash')

app.config.update(
	DEBUG = True,
	SECRET_KEY = 'dev',
	LOG_FILE = None,
	LOG_FORMAT = '%(asctime)s %(name)s\t%(levelname)s\t%(message)s',
	LOG_LEVEL = logging.INFO,
)

login_manager = flask.ext.login.LoginManager(app)

api = chef.autoconfigure()

def handler(environ, start_response):
	handled = False
	if environ['PATH_INFO'].startswith('/feed/'):
		ws = environ.get('wsgi.websocket')
		if ws:
			handle_websocket(ws, environ['PATH_INFO'][6:])
			handled = True
	
	if not handled:
		return app(environ, start_response)

websockets = {}

def handle_websocket(ws, env):
	s = websockets.get(env)
	if s is None:
		s = websockets[env] = []
	s.append(ws)

	while True:
		buf = ws.receive()
		if buf is None:
			break

	if ws in s:
		s.remove(ws)

@app.route('/feed/<env>')
@flask.ext.login.login_required
def feed(env = None):
	flask.abort(400)

greenlets = {}

def executing_processes(env = None, node = None):
	env_greenlets = greenlets.get(env)
	if env_greenlets is None:
		return 0
	elif node is None:
		result = 0
		for greenlet in env_greenlets.itervalues():
			if not greenlet.ready():
				result += 1
		return result
	else:
		greenlet = env_greenlets.get(node)
		if greenlet is None or greenlet.ready():
			return 0
		else:
			return 1

def broadcast(env, packet):
	sockets = websockets.get(env)
	if sockets is not None:
		packet = ujson.encode(packet)
		for ws in list(sockets):
			if ws.socket is not None:
				try:
					ws.send(packet)
				except gevent.socket.error:
					if ws in sockets:
						sockets.remove(ws)

@app.route('/converge/<env>', methods = ['POST'])
@app.route('/converge/<env>/<node>', methods = ['POST'])
@flask.ext.login.login_required
def converge(env = None, node = None):
	if env is None and node is None:
		flask.abort(400)

	if executing_processes(env, node) > 0:
		return ujson.encode({ 'status': 'converging' })
	else:
		env_greenlets = greenlets.get(env)
		if env_greenlets is None:
			greenlets[env] = env_greenlets = { }

		if node is not None:
			nodes = [chef.Node(node, api = api)]
			if node in env_greenlets:
				del env_greenlets[node]
		else:
			nodes = chef.Search('node', 'chef_environment:' + env, api = api)
			env_greenlets.clear()

		for n in nodes:
			if not isinstance(n, chef.Node):
				n = n.object
			p = subprocess.Popen(['ssh', '-o', 'StrictHostKeyChecking=no', n['ipaddress'], 'sudo', 'chef-client'], shell = False, stdout = subprocess.PIPE)
			p.chunks = []
			fcntl.fcntl(p.stdout, fcntl.F_SETFL, os.O_NONBLOCK)  # make the file nonblocking

			def read(host, process):
				broadcast(env, { 'host': host, 'status': 'converging' })

				while True:
					chunk = None
					try:
						chunk = process.stdout.read(4096)
						if not chunk:
							break

					except IOError, e:
						chunk = None
						if e[0] != errno.EAGAIN:
							raise
						sys.exc_clear()

					if chunk:
						process.chunks.append(chunk)
						broadcast(env, { 'host': host, 'data': chunk, })

					gevent.socket.wait_read(process.stdout.fileno())

				process.stdout.close()

				process.wait()

				broadcast(env, { 'host': host, 'status': 'ready' if process.returncode == 0 else 'error' })

				if executing_processes(env) <= 1:
					broadcast(env, { 'status': 'ready' })

				return process.returncode

			greenlet = gevent.spawn(read, host = n.name, process = p)
			greenlet.process = p
			env_greenlets[n.name] = greenlet

		broadcast(env, { 'status': 'converging' })

		return ujson.encode({ 'status': 'converging' if len(nodes) > 0 else 'ready' })

@app.route('/')
@flask.ext.login.login_required
def index():
	envs = chef.Environment.list(api = api)
	return flask.render_template(
		'index.html',
		envs = envs.itervalues(),
	)

@app.route('/<env>')
@flask.ext.login.login_required
def env(env):
	nodes = list(chef.Search('node', 'chef_environment:%s' % env, api = api))
	nodes.sort(key = lambda node: node.object.name)

	env_greenlets = greenlets.get(env)
	if env_greenlets is None:
		env_greenlets = greenlets[env] = { }

	status = {}
	output = {}
	for node in nodes:
		greenlet = env_greenlets.get(node.object.name)
		if greenlet is None:
			status[node.object.name] = 'ready'
			output[node.object.name] = ''
		else:
			s = 'converging'
			if greenlet.ready():
				s = 'ready' if greenlet.value == 0 else 'error'
			status[node.object.name] = s
			output[node.object.name] = ''.join(greenlet.process.chunks)

	return flask.render_template(
		'env.html',
		env = env,
		converging = executing_processes(env) > 0,
		status = status,
		output = output,
		nodes = nodes,
	)

@login_manager.user_loader
class User(object):
	def __init__(self, id):
		self.id = id
	
	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.id

	#def get_auth_token(self):
		#return flask.ext.login.make_secure_token(self.id)

login_manager.login_view = 'login'

@app.template_filter('urlquote')
def urlquote(url):
	return urllib.quote(url, '')

@app.route('/login', methods = ['GET', 'POST'])
def login():
	if flask.ext.login.current_user.is_authenticated():
		return flask.redirect(request.args.get('next') or flask.url_for('index'))

	username = flask.request.form.get('username')
	remember = flask.request.form.get('remember') == 'on'

	if username is not None:

		password = flask.request.form.get('password')

		auth_result = ujson.decode(api.request('POST', '/authenticate_user', data = ujson.encode({ 'name': username, 'password': password })))

		if auth_result.get('name') == username and auth_result.get('verified'):

			flask.ext.login.login_user(User(username), remember = remember)

			return flask.redirect(flask.request.args.get('next') or flask.url_for('index'))

		else:
			return flask.render_template('login.html',
				username = username,
				error = True,
				remember = remember,
				next = flask.request.args.get('next'),
			)

	return flask.render_template('login.html',
		username = None,
		error = False,
		remember = remember,
		next = flask.request.args.get('next'),
	)

@app.route('/logout')
def logout():
	flask.ext.login.logout_user()
	return flask.redirect(flask.url_for('login'))

@app.route('/favicon.ico')
def favicon():
	return flask.send_from_directory(
		os.path.join(app.root_path, 'static'),
		'favicon.ico',
		mimetype = 'image/vnd.microsoft.icon',
	)
