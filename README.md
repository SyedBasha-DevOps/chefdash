chefdash
========

chefdash is a simple dashboard for tracking [Chef](http://www.opscode.com/chef/) runs across a cluster.

With chefdash you can:

* Run `chef-client` on all nodes in a Chef environment simultaneously, or on a single node
* View output in realtime and quickly see if any nodes failed

Install
-------

1. **Clone the source and run the install script** (only works on Ubuntu for now)

	__Warning__: the install script attempts to install nginx 1.4 or higher from the nginx deb repo. If you already have an older version of nginx installed, you'll need to remove it. (1.4 is required for websocket proxying)

	```shell
	sudo apt-get install git
	git clone <source url> chefdash
	cd chefdash
	sudo ./install.sh
	```

	*__Note__: the install script is __idempotent__, which means if you want to upgrade to the latest chefdash, you can just `git pull` and run the script again.*

2. **Login as the newly created `chefdash` user**

	```shell
	sudo -i -u chefdash
	```

3. **Configure access to the Chef server**

	If you already have a working knife configuration, just copy your `.chef` folder into the `chefdash` home folder (which is `/var/lib/chefdash`). Otherwise, set up knife according to Opscode's [instructions](http://docs.opscode.com/knife_configure.html):

	```shell
	knife configure --initial
	```

4. **Configure SSH**

	Make sure the chefdash user has the ability to SSH into the nodes as root without a password:

	```shell
	ssh-keygen
	cat ~/.ssh/id_rsa.pub # Copy this public key into the /root/.ssh/authorized_keys file on each node
	```

	> Worried about passwordless root access? Create a `chefdash` user on each of your nodes, then put this line in the `/etc/sudoers` file:
	>
	> ```shell
	> chefdash ALL=(ALL) NOPASSWD: /usr/bin/chef-client
	> ```
	> 
	> This will allow the chefdash user to only execute `chef-client` as root.

	chefdash doesn't know what user to login as on your nodes. [Configure SSH](http://nerderati.com/2011/03/simplify-your-life-with-an-ssh-config-file/) to automatically fill in the correct usernames:

	```shell
	vim ~/.ssh/config
	# Sample configuration telling SSH to login as  user "ubuntu" on all nodes:
	# Host *
	#   User ubuntu
	```

6. **Finish up**

	`exit` out of the chefdash shell, then restart the chefdash service:

	```shell
	sudo service chefdash restart
	```

You're all set!
