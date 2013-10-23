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
git clone <source url> chefdash
cd chefdash
sudo ./install.sh
```

Login as the newly created `chefdash` user:

```shell
sudo -i -u chefdash
```

Set up knife according to the instructions_:

```shell
knife configure --initial
```

Make sure the chefdash user has the ability to SSH into the nodes as root without a password:

```shell
ssh-keygen
cat ~/.ssh/id_rsa.pub # Copy this public key into the /root/.ssh/authorized_keys file on each node
```

You're all set!

.. _instructions: http://docs.opscode.com/knife_configure.html
