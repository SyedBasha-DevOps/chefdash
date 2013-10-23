#!/bin/bash

set -u
set -e

# Run this as root
if [[ $EUID -ne 0 ]]; then
	echo 'You must be root to install chefdash.' 2>&1
	exit 1
fi

# Install package dependencies
apt-get update
apt-get -y install build-essential python-dev libevent-dev python-pip nginx

# Install python dependencies
pip install -r requirements.txt

# Install chefdash
python setup.py install

# Upstart configuration
cp -f upstart/chefdash.conf /etc/init/

# nginx configuration
cp -f nginx/chefdash.conf /etc/nginx/sites-available
ln -fs /etc/nginx/sites-available/chefdash.conf /etc/nginx/sites-enabled/chefdash.conf

# User

id -u chefdash &>/dev/null || useradd chefdash -r -m -s/bin/bash

# Config directory

mkdir -p /etc/chefdash

# Generate secret key and insert into the config file if necessary
secret_key=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
[ -f /etc/chefdash/chefdash.py ] || (echo "SECRET_KEY='$secret_key'" > /etc/chefdash/chefdash.py)
chmod 0600 /etc/chefdash/chefdash.py
chown -R chefdash:chefdash /etc/chefdash

# Log directory
mkdir -p /var/log/chefdash
chown -R chefdash:chefdash /var/log/chefdash

# Restart upstart services
service chefdash restart
service nginx restart
