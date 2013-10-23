import gevent
import gevent.monkey
import gevent.socket
gevent.monkey.patch_all()

import subprocess
import fcntl
import os
import errno
import sys
import ujson

import gevent.queue
import gevent.event

import flask
import chef

app = flask.Flask('chefdash')

api = chef.autoconfigure()

app.debug = True

def handler(environ, start_response):
	handled = False
	if environ['PATH_INFO'] == '/feed':
		ws = environ.get('wsgi.websocket')
		if ws:
			handle_websocket(ws)
			handled = True
	
	if not handled:
		return app(environ, start_response)

websockets = []

def handle_websocket(ws):
	websockets.append(ws)

	while True:
		buf = ws.receive()
		if buf is None:
			break

	if ws in websockets:
		websockets.remove(ws)

@app.route('/feed')
def feed():
	flask.abort(400)

greenlets = {}

def executing_processes(env = None):
	env_greenlets = greenlets.get(env)
	if env_greenlets is None:
		return 0
	else:
		result = 0
		for greenlet in env_greenlets.itervalues():
			if not greenlet.ready():
				result += 1
		return result

def broadcast(packet):
	packet = ujson.encode(packet)
	for ws in list(websockets):
		if ws.socket is not None:
			try:
				ws.send(packet)
			except gevent.socket.error:
				if ws in websockets:
					websockets.remove(ws)

@app.route('/converge/<env>', methods = ['POST'])
@app.route('/converge/<env>/<node>', methods = ['POST'])
def converge(env = None, node = None):
	if env is None and node is None:
		flask.abort(400)

	if executing_processes(env) > 0:
		return ujson.encode({ 'status': 'converging' })
	else:
		env_greenlets = greenlets.get(env)
		if env_greenlets is None:
			greenlets[env] = env_greenlets = { }
		else:
			env_greenlets.clear()

		if node is not None:
			nodes = [Node(node)]
		else:
			nodes = chef.Search('node', 'chef_environment:' + env, api = api)

		for n in nodes:
			p = subprocess.Popen(['ssh', n.object['ipaddress'], 'sudo', 'chef-client'], shell = False, stdout = subprocess.PIPE)
			p.chunks = []
			fcntl.fcntl(p.stdout, fcntl.F_SETFL, os.O_NONBLOCK)  # make the file nonblocking

			def read(host, process):
				broadcast({ 'host': host, 'status': 'converging' })

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
						broadcast({ 'host': host, 'data': chunk, })

					gevent.socket.wait_read(process.stdout.fileno())

				process.stdout.close()

				process.wait()

				broadcast({ 'host': host, 'status': 'ready' if process.returncode == 0 else 'error' })

				if executing_processes(env) <= 1:
					broadcast({ 'status': 'ready' })

				return process.returncode

			greenlet = gevent.spawn(read, host = n.object.name, process = p)
			greenlet.process = p
			env_greenlets[n.object.name] = greenlet

		broadcast({ 'status': 'converging' })

		return ujson.encode({ 'status': 'converging' if len(nodes) > 0 else 'ready' })

@app.route('/')
def index():
	envs = chef.Environment.list(api = api)
	return flask.render_template(
		'index.html',
		envs = envs.itervalues(),
	)

@app.route('/<env>')
def env(env):
	nodes = chef.Search('node', 'chef_environment:%s' % env, api = api)

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
