.. _elhaz-config-update:

``elhaz config update``
=======================

Synopsis
--------

.. code-block:: text

   elhaz config update [OPTIONS]

Description
-----------

Update an existing config. You may choose to walk through the interactive
prompts (with existing values pre-populated) or open the YAML file directly in
your ``$EDITOR``. elhaz re-validates the full config before saving.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Update a config interactively:

.. code-block:: bash

   elhaz config update -n prod

Open a config in your editor:

.. code-block:: bash

   elhaz config update -n staging
   # When prompted "Edit interactively?", select No.
   # Your $EDITOR opens with the existing YAML file.
