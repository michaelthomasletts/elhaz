.. _elhaz-daemon-start:

``elhaz daemon start``
======================

Synopsis
--------

.. code-block:: text

   elhaz daemon start

Description
-----------

Launch the daemon as a detached background process. elhaz waits up to 5
seconds for the daemon to become reachable on its socket before reporting
success or failure.

If the daemon is already running, this command exits immediately with a
notice.

All global options passed to ``elhaz`` (e.g. ``--socket-path``,
``--max-daemon-cache-size``) are forwarded to the daemon process so both sides
share the same configuration.

Options
-------

``--help``
   Show help message and exit.

Examples
--------

Start the daemon with default settings:

.. code-block:: bash

   elhaz daemon start

Start the daemon with a custom socket and larger cache:

.. code-block:: bash

   elhaz --socket-path /tmp/elhaz.sock --max-daemon-cache-size 25 daemon start

.. seealso::

   :ref:`elhaz daemon stop <elhaz-daemon-stop>` — gracefully stop the daemon.
