chefdash
========

chefdash is a simple dashboard for tracking Chef_ runs across a cluster.

With chefdash you can:

* Run `chef-client` on all nodes in a Chef environment simultaneously, or on a single node
* View output in realtime and quickly see if any nodes failed

Install
-------

Clone the source and run the install script (only works on Ubuntu for now):

```shell
sudo apt-get install git
git clone <source url> chefdash
cd chefdash
sudo ./install.sh
```

Login as the newly created `chefdash` user:

```shell
sudo -i -u chefdash
```

If you already have a working knife configuration, just copy your `.chef` folder into the `chefdash` home folder (which is `/var/lib/chefdash`). Otherwise, set up knife according to Opscode's instructions_:

```shell
knife configure --initial
```

Make sure the chefdash user has the ability to SSH into the nodes as root without a password:

```shell
ssh-keygen
cat ~/.ssh/id_rsa.pub # Copy this public key into the /root/.ssh/authorized_keys file on each node
```

`exit` out of the chefdash shell, then restart the chefdash service:
```shell
sudo service chefdash restart
```

You're all set!

.. _Chef: http://www.opscode.com/chef/
.. _instructions: http://docs.opscode.com/knife_configure.html
