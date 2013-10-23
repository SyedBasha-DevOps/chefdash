#!/usr/bin/env python

import chefdash

if __name__ == '__main__':
	import geventwebsocket.handler
	import gevent.pywsgi
	import logging
	import sys

	if sys.argc > 1:
		chefdash.app.config.from_pyfile(sys.argv[1])

	host = 'localhost'
	port = 5000

	server_name = chefdash.app.config['SEVER_NAME']
	if ':' in server_name:
		server_name = server_name.split(':')
		host = server_name[0]
		port = int(server_name[1])

	logging.basicConfig(filename = chefdash.app.config['LOG_FILE'], level = logging.INFO)

	server = gevent.pywsgi.WSGIServer((host, port), chefdash.handler, handler_class = geventwebsocket.handler.WebSocketHandler)
	server.serve_forever()
