.. _elhaz-daemon-add:

``elhaz daemon add``
====================

Synopsis
--------

.. code-block:: text

   elhaz daemon add [OPTIONS]

Description
-----------

Initialize an AWS session for the named config and add it to the daemon's
session cache. If the cache is full, the least recently used session is
evicted to make room.

The daemon must be running before calling this command.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Add a session by config name:

.. code-block:: bash

   elhaz daemon add -n prod

Select a config interactively:

.. code-block:: bash

   elhaz daemon add

.. seealso::

   :ref:`elhaz daemon remove <elhaz-daemon-remove>` — remove a session from
   the cache without stopping the daemon.
