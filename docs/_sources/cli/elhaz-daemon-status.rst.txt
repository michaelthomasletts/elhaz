.. _elhaz-daemon-status:

``elhaz daemon status``
=======================

Synopsis
--------

.. code-block:: text

   elhaz daemon status

Description
-----------

Report whether the elhaz daemon is currently reachable on its UNIX socket.

If the daemon is running, the command prints a confirmation and the socket path,
then exits with code 0. If the daemon is not running, it exits with code 1.
The non-zero exit code makes ``status`` useful in shell scripts and ``&&``
chains.

Options
-------

``--help``
   Show help message and exit.

Examples
--------

Check whether the daemon is running:

.. code-block:: bash

   elhaz daemon status

Use in a shell conditional:

.. code-block:: bash

   elhaz daemon status || elhaz daemon start

.. seealso::

   :ref:`elhaz daemon start <elhaz-daemon-start>` — start the daemon.

   :ref:`elhaz daemon stop <elhaz-daemon-stop>` — stop the daemon.
