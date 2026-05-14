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

``--obscure``, ``-o``
   Redact sensitive field values in the output. Affected fields include
   ``RoleArn``, ``ExternalId``, ``SerialNumber``, ``TokenCode``,
   ``PolicyArns``, and any static AWS credentials
   (``aws_access_key_id``, ``aws_secret_access_key``, ``aws_session_token``,
   ``aws_account_id``). Redacted values are replaced with ``***``.
   Off by default.

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

Print a config with sensitive values hidden (e.g. for screen sharing):

.. code-block:: bash

   elhaz config get -n prod --obscure
