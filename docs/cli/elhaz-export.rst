.. _elhaz-export:

``elhaz export``
================

Synopsis
--------

.. code-block:: text

   elhaz export [OPTIONS]

Description
-----------

Export temporary AWS credentials for the named config. If no active session
exists for the config, elhaz adds it to the daemon automatically before
exporting.

Three output formats are available:

``json`` (default)
   Prints the raw credentials dict with ``access_key``, ``secret_key``,
   ``token``, and ``expiry_time`` fields.

``env``
   Prints ``export KEY=VALUE`` lines suitable for ``eval``. Sets
   ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, ``AWS_SESSION_TOKEN``,
   and ``AWS_CREDENTIAL_EXPIRATION``.

``credential-process``
   Prints a JSON object matching the shape required by AWS
   ``credential_process`` profile entries.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--format``, ``-f`` ``json`` | ``env`` | ``credential-process``
   Output format. Default: ``json``.

``--help``
   Show help message and exit.

Examples
--------

Export as JSON:

.. code-block:: bash

   elhaz export -n prod

Source env vars into the current shell:

.. code-block:: bash

   eval $(elhaz export -n prod -f env)

Use elhaz as an AWS ``credential_process`` provider in ``~/.aws/config``:

.. code-block:: ini

   [profile my-role]
   credential_process = elhaz export -n prod -f credential-process
