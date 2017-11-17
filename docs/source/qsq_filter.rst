qsq filter
==========

The output of several ``qsq`` command uses json format and one of the reasons
is to be able to filter the contents using  `jmespath`_.

``qsq filter`` command is just a simple wrapper around jmespath library, but
more advanced options are available, like `jpterm`_.


Usage
-----

Consider the json below (saved as ``example.json``):

.. code:: json

    {
        "queues": [
            {
                "name": "queue-one",
                "count": 2
            },
            {
                "name": "queue-two",
                "count": 0
            }
        ]
    }


We can filter only the ``"name"`` values using the following:


.. code:: bash

    # piping contents to qsq filter
    $ cat example.json | qsq filter 'queues[].name'
    [
        "queue-one",
        "queue-two"
    ]

    # or using the filename
    $ qsq filter 'queue[].name' example.json
    [
        "queue-one",
        "queue-two"
    ]


.. _jmespath: http://jmespath.org/
.. _jpterm: https://github.com/jmespath/jmespath.terminal
