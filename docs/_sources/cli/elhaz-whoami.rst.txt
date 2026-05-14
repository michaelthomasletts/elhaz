.. _elhaz-whoami:

``elhaz whoami``
================

Synopsis
--------

.. code-block:: text

   elhaz whoami [OPTIONS]

Description
-----------

Return the STS caller identity for the named config as formatted JSON. The
response includes ``Account``, ``Arn``, and ``UserId``.

If no active session exists for the config, elhaz prompts you to add it to the
daemon before retrying.

The daemon must be running before calling this command.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--obscure``, ``-o``
   Redact sensitive identity values in the output. The ``Account``, ``Arn``,
   and ``UserId`` fields are replaced with ``***``. Off by default.

``--help``
   Show help message and exit.

Examples
--------

Check identity for a config:

.. code-block:: bash

   elhaz whoami -n prod

Example output:

.. code-block:: json

   {
     "UserId": "AROAEXAMPLEID:session-name",
     "Account": "123456789012",
     "Arn": "arn:aws:sts::123456789012:assumed-role/MyRole/session-name"
   }

Check identity with sensitive values hidden (e.g. for screen sharing):

.. code-block:: bash

   elhaz whoami -n prod --obscure
