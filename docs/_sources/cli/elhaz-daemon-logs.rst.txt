.. _elhaz-daemon-logs:

``elhaz daemon logs``
=====================

Synopsis
--------

.. code-block:: text

   elhaz daemon logs [OPTIONS]

Description
-----------

Print daemon log output from the log file at ``~/.elhaz/logs/daemon.log`` (or
the path set by ``--logging-path``). Defaults to the last 50 lines.

Options
-------

``--tail``, ``-t`` *INTEGER*
   Show the last *N* lines. Default: ``50``. Pass ``0`` to print the entire
   file.

``--head``, ``-h`` *INTEGER*
   Show the first *N* lines. If set, ``--tail`` is ignored.

``--help``
   Show help message and exit.

Examples
--------

Show the last 50 lines (default):

.. code-block:: bash

   elhaz daemon logs

Show the last 100 lines:

.. code-block:: bash

   elhaz daemon logs -t 100

Show the first 20 lines:

.. code-block:: bash

   elhaz daemon logs --head 20

Print the entire log file:

.. code-block:: bash

   elhaz daemon logs -t 0
