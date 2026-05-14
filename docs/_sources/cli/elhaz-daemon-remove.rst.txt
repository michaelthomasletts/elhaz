.. _elhaz-daemon-remove:

``elhaz daemon remove``
=======================

Synopsis
--------

.. code-block:: text

   elhaz daemon remove [OPTIONS]

Description
-----------

Remove an active session from the daemon's session cache. The corresponding
config file is not affected.

The daemon must be running before calling this command.

Options
-------

``--name``, ``-n`` *NAME*
   Session name. If omitted, an interactive selection prompt lists active
   sessions from the daemon's cache.

``--help``
   Show help message and exit.

Examples
--------

Remove a session by name:

.. code-block:: bash

   elhaz daemon remove -n prod

Select a session to remove interactively:

.. code-block:: bash

   elhaz daemon remove
