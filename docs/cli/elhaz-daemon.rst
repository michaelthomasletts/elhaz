.. _elhaz-daemon:

``elhaz daemon``
================

Synopsis
--------

.. code-block:: text

   elhaz daemon COMMAND [ARGS]...

Description
-----------

Manage the elhaz daemon. The daemon is a background process that holds a
bounded LRU cache of active AWS sessions and serves credential requests over a
UNIX domain socket.

For a conceptual overview of the daemon, see :ref:`Daemon <daemon>`.

Options
-------

``--help``
   Show help message and exit.

Commands
--------

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - :ref:`add <elhaz-daemon-add>`
     - Initialize a session and add it to the daemon's cache.
   * - :ref:`kill <elhaz-daemon-kill>`
     - Forcefully stop the daemon (alias for ``stop``).
   * - :ref:`list <elhaz-daemon-list>`
     - List all active sessions in the daemon's cache.
   * - :ref:`logs <elhaz-daemon-logs>`
     - Print daemon log output.
   * - :ref:`remove <elhaz-daemon-remove>`
     - Remove an active session from the daemon's cache.
   * - :ref:`start <elhaz-daemon-start>`
     - Start the daemon in the background.
   * - :ref:`status <elhaz-daemon-status>`
     - Report whether the daemon is currently running.
   * - :ref:`stop <elhaz-daemon-stop>`
     - Stop the running daemon gracefully.

.. toctree::
   :hidden:

   elhaz daemon add <elhaz-daemon-add>
   elhaz daemon kill <elhaz-daemon-kill>
   elhaz daemon list <elhaz-daemon-list>
   elhaz daemon logs <elhaz-daemon-logs>
   elhaz daemon remove <elhaz-daemon-remove>
   elhaz daemon start <elhaz-daemon-start>
   elhaz daemon status <elhaz-daemon-status>
   elhaz daemon stop <elhaz-daemon-stop>
