.. _elhaz-config-get:

``elhaz config get``
====================

Synopsis
--------

.. code-block:: text

   elhaz config get [OPTIONS]

Description
-----------

Display a config as formatted, syntax-highlighted JSON. If the config does not
exist and you are running in an interactive terminal, elhaz will offer to
create it.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Print a config by name:

.. code-block:: bash

   elhaz config get -n prod

Select a config interactively:

.. code-block:: bash

   elhaz config get
