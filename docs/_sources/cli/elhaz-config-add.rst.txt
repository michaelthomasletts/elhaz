.. _elhaz-config-add:

``elhaz config add``
====================

Synopsis
--------

.. code-block:: text

   elhaz config add [OPTIONS]

Description
-----------

Create a new config in the local config store. When prompted, you may choose
to build the config interactively using step-by-step prompts, or open it
directly in your ``$EDITOR`` (defaulting to ``vi``).

elhaz validates all data types before writing, but does not verify correctness
against AWS (e.g. whether an ARN is valid). The only required field is
``RoleArn`` under ``AssumeRole``.

If a config with the same name already exists, elhaz will ask whether to
overwrite it.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Create a config interactively:

.. code-block:: bash

   elhaz config add -n prod

Create a config using your editor:

.. code-block:: bash

   elhaz config add -n staging
   # When prompted "Create config interactively?", select No.
   # Your $EDITOR opens with an empty YAML file.

.. seealso::

   :ref:`Config <config>` — full reference for all config parameters.
