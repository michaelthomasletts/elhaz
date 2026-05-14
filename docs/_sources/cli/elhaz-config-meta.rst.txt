.. _elhaz-config-meta:

``elhaz config meta``
=====================

Synopsis
--------

.. code-block:: text

   elhaz config meta [OPTIONS]

Description
-----------

Print the :ref:`Meta <meta>` section of a config as formatted, syntax-highlighted
JSON. If the config exists but has no ``Meta`` section, a plain message is printed
and the command exits successfully.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Print metadata for a config by name:

.. code-block:: bash

   elhaz config meta -n prod

Select a config interactively:

.. code-block:: bash

   elhaz config meta
