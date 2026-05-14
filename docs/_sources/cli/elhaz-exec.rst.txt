.. _elhaz-exec:

``elhaz exec``
==============

Synopsis
--------

.. code-block:: text

   elhaz exec [OPTIONS] -- COMMAND [ARGS]...

Description
-----------

Execute a one-off command with AWS credentials injected as environment
variables. The following variables are set for the child process:

- ``AWS_ACCESS_KEY_ID``
- ``AWS_SECRET_ACCESS_KEY``
- ``AWS_SESSION_TOKEN``

If no active session exists for the named config, elhaz adds it to the daemon
automatically before running the command.

The ``--`` separator is required to distinguish elhaz options from the
command being executed.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Run an AWS CLI command:

.. code-block:: bash

   elhaz exec -n prod -- aws s3 ls

Copy a file from S3:

.. code-block:: bash

   elhaz exec -n prod -- aws s3 cp s3://my-bucket/file.txt .

Run any arbitrary command with credentials in scope:

.. code-block:: bash

   elhaz exec -n prod -- python my_script.py

.. seealso::

   :ref:`elhaz shell <elhaz-shell>` — for running multiple commands in a
   persistent credential environment.
