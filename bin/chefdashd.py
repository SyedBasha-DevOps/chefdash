#!/usr/bin/env python

import chefdash

if __name__ == '__main__':
	import geventwebsocket.handler
	import gevent.pywsgi
	server = gevent.pywsgi.WSGIServer(('', 8080), chefdash.handler, handler_class = geventwebsocket.handler.WebSocketHandler)
	server.serve_forever()
