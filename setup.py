#!/usr/bin/python
from setuptools import setup

setup(
	name = 'chefdash',
	version = '0.1.0',
	author = 'Sidebolt Studios',
	author_email = 'contact@sidebolt.com',
	scripts = ['bin/chefdashd.py',],
	packages = [
		'chefdash',
	],
	url = 'http://github.com/sidebolt/chefdash/',
	description = 'Chef Dash'
)
