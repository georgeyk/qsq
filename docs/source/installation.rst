Installation
============

Requirements
------------

Python 3.5+

To install via pip::

    $ pip install qsq


Basic configuration
-------------------


To configure AWS access, check `boto3 configuration`_ or export (see `boto3 envvars`_)::

    $ export AWS_ACCESS_KEY_ID=<key>
    $ export AWS_SECRET_ACCESS_KEY=<secret>
    $ export AWS_DEFAULT_REGION=sa-east-1  # for example

It is a good practice to create specific users with restricted permissions.
Try not to use your person keys with ``qsq``.


Basic Usage
-----------

At this point you can check the available commands and their description::

    $ qsq --help


.. _boto3 configuration: https://boto3.readthedocs.org/en/latest/guide/quickstart.html#configuration
.. _boto3 envvars: http://boto3.readthedocs.org/en/latest/guide/configuration.html#environment-variable-configuration
