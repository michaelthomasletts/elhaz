.. _elhaz-config-remove:

``elhaz config remove``
=======================

Synopsis
--------

.. code-block:: text

   elhaz config remove [OPTIONS]

Description
-----------

Delete a config from the local config store. A confirmation prompt is shown
before the file is removed. This operation cannot be undone.

.. note::

   Removing a config does not remove the corresponding session from the
   daemon's cache. Use :ref:`elhaz daemon remove <elhaz-daemon-remove>` to
   remove the session from the daemon separately.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Remove a config by name:

.. code-block:: bash

   elhaz config remove -n prod

Select a config to remove interactively:

.. code-block:: bash

   elhaz config remove
