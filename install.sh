#!/bin/bash

set -u
set -e

# Run this as root
if [[ $EUID -ne 0 ]]; then
	echo 'You must be root to install chefdash.' 2>&1
	exit 1
fi

# Install package dependencies
sudo add-apt-repository 'deb http://nginx.org/packages/ubuntu/ precise nginx'
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys ABF5BD827BD9BF62
apt-get update
apt-get -y install build-essential python-dev libevent-dev python-pip nginx

# Install python dependencies
pip install -r requirements.txt

# Install chefdash
python setup.py install

# Upstart configuration
cp -f upstart/chefdash.conf /etc/init/

# nginx configuration
rm -f /etc/nginx/conf.d/default.conf
cp -f nginx/chefdash.conf /etc/nginx/conf.d/

# User

id -u chefdash &>/dev/null || useradd chefdash -r -d/var/lib/chefdash -m -s/bin/bash

# Config directory

mkdir -p /etc/chefdash

# Generate secret key and insert into the config file if necessary
secret_key=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
[ -f /etc/chefdash/chefdash.py ] || (echo "SECRET_KEY='$secret_key'" > /etc/chefdash/chefdash.py)
chmod 0600 /etc/chefdash/chefdash.py
chown -R chefdash:chefdash /etc/chefdash

# SSL certificates
if [ ! -f /var/lib/chefdash/server.crt ];
then
	openssl genrsa -out /var/lib/chefdash/ssl.key 2048
	openssl req -new -key /var/lib/chefdash/ssl.key -out /var/lib/chefdash/ssl.csr
	openssl x509 -req -days 7304 -in /var/lib/chefdash/ssl.csr -signkey /var/lib/chefdash/ssl.key -out /var/lib/chefdash/ssl.crt
	chown nginx:nginx /var/lib/chefdash/ssl.*
fi

# Log directory
mkdir -p /var/log/chefdash
chown -R chefdash:chefdash /var/log/chefdash

# Restart upstart services
service chefdash restart
service nginx restart
