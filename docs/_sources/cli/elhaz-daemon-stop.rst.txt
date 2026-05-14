.. _elhaz-daemon-stop:

``elhaz daemon stop``
=====================

Synopsis
--------

.. code-block:: text

   elhaz daemon stop

Description
-----------

Send a graceful shutdown request to the running daemon and wait up to 5
seconds for it to exit. All active sessions are discarded when the daemon
stops.

If the daemon is not running, this command exits immediately with a notice.

Options
-------

``--help``
   Show help message and exit.

Examples
--------

.. code-block:: bash

   elhaz daemon stop

.. seealso::

   :ref:`elhaz daemon kill <elhaz-daemon-kill>` — alias for this command.
