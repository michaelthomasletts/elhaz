.. _elhaz-shell:

``elhaz shell``
===============

Synopsis
--------

.. code-block:: text

   elhaz shell [OPTIONS]

Description
-----------

Spawn an interactive shell with auto-refreshed AWS credentials. elhaz sets
``AWS_CREDENTIAL_PROCESS`` so AWS SDKs transparently fetch fresh credentials
from the daemon on every API call. Initial credentials are also exported as
environment variables for immediate use.

Shell-specific behavior:

**bash / sh**
   ``PROMPT_COMMAND`` is set to re-export credentials before each prompt,
   keeping ``AWS_ACCESS_KEY_ID``, ``AWS_SECRET_ACCESS_KEY``, and
   ``AWS_SESSION_TOKEN`` current in the environment.

**zsh**
   ``PROMPT_COMMAND`` is not natively supported. elhaz exports an
   ``ELHAZ_PRECMD`` variable containing the refresh command and prints a tip
   at startup. To enable automatic refresh, wire it up in your precmd hook:

   .. code-block:: zsh

      precmd_functions+=(elhaz_precmd)
      elhaz_precmd() { eval $ELHAZ_PRECMD }

Exit the shell at any time with ``exit`` to return to the original
environment.

Options
-------

``--name``, ``-n`` *NAME*
   Config name. If omitted, an interactive selection prompt is shown.

``--help``
   Show help message and exit.

Examples
--------

Spawn a shell with credentials for a config:

.. code-block:: bash

   elhaz shell -n prod
   aws s3 ls
   aws sts get-caller-identity
   exit

Select a config interactively:

.. code-block:: bash

   elhaz shell

.. seealso::

   :ref:`elhaz exec <elhaz-exec>` — for running a single command without
   opening an interactive shell.
