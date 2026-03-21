.. _quickstart:

Quickstart
==========

elhaz can be used locally to manage automatically refreshed temporary AWS credentials for *multiple* IAM roles simultaneously.
Those credentials can be passed to AWS profiles, SDKs, CLIs, scripts, processes, local developer environments, and tools in a variety of creative ways.

To quickly get started using elhaz, follow this basic guide.

For more detailed information on all of the available commands and options, see the :ref:`cli` documentation.

Initialization
--------------

.. tip::

    To see all of the available commands and options, use ``--help`` on any command.

In order to use elhaz, you must set up at least one config. 

A config represents a set of parameters that `boto3-refresh-session <https://github.com/61418/boto3-refresh-session>`_ uses in order to initialize an AWS session which automatically refreshes temporary AWS credentials.

.. tip::

    You can also create configs manually by hand if you prefer. 
    However, the easiest way to create a config is to use the interactive prompts provided by elhaz as shown below.

    The default location for configs is ``~/.elhaz/configs/``.
    Each config is a YAML file with any name you choose with a ``.yaml`` extension.
.. code-block:: bash

    elhaz config add

``elhaz config add`` will present you with a set of interactive prompts which help you create the config piece by piece. 

.. tip::

    The only required config parameter is ``RoleArn``. 
    All other parameters are completely optional.

.. tip::

    You can edit, view, and delete configs at any time.
    Check available commands by entering ``elhaz config --help``.

Next, you must initialize the elhaz daemon.

.. code-block:: bash

    elhaz daemon start

In order to use the config you just created, you must initialize the AWS session for your config and add it into the daemon's session cache.

.. code-block:: bash
    
    elhaz daemon add -n <your config name>

Commands
--------

Export the automatically refreshed temporary AWS credenitals from your config to stdout.

.. code-block:: bash
    
    elhaz export -n <your config name>


Or export env vars.

.. code-block:: bash

    elhaz export -n <your config name> -f env

Or export the credentials in a format compatible with `credential_process` in your AWS profile.

.. code-block:: ini

   [profile my-role]
   credential_process = elhaz export -n <your config name> -f credential-process

You may also execute a one-off AWS CLI command using the config's credentials.

.. code-block:: bash

    elhaz exec -n <your config name> --- aws s3 ls

Or initialize a shell and run as many AWS commands as you want for however long you like.

.. tip::

    The shell can be terminated by entering ``exit``.

.. code-block:: bash

    elhaz shell -n <your config name>
    aws s3 ls
    aws s3 cp s3://my-bucket/my-file.txt .
    ...

If you forget who you are, fret not.

.. code-block:: bash

    elhaz whoami -n <your config name>

You can also read the logs from the daemon.

.. code-block:: bash

    elhaz daemon logs

You can also list all active AWS sessions in the daemon's session cache.

.. code-block:: bash

    elhaz daemon list

Shutdown
--------

When you're done working, stop the daemon.

.. code-block:: bash

    elhaz daemon stop