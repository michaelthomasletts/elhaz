.. _elhaz:

``elhaz``
=========

Synopsis
--------

.. code-block:: text

   elhaz [OPTIONS] COMMAND [ARGS]...

Description
-----------

Root command. All global options listed here apply to every subcommand and are
forwarded verbatim to the daemon process when ``elhaz daemon start`` is called,
ensuring both sides share the same configuration.

Options
-------

``--config-dir``, ``-cd`` *PATH*
   Config directory. Default: ``~/.elhaz/configs``.

``--socket-path``, ``-sp`` *PATH*
   UNIX socket path for daemon communication.
   Default: ``~/.elhaz/sock/daemon.sock``.

``--logging-path``, ``-lp`` *PATH*
   Daemon log file path. Default: ``~/.elhaz/logs/daemon.log``.

``--max-unix-socket-connections``, ``-musc`` *INTEGER*
   Maximum number of pending UNIX socket connections in the daemon's listen
   backlog. Default: ``5``.

``--max-daemon-cache-size``, ``-mdcs`` *INTEGER*
   Maximum number of sessions the daemon will retain in its LRU cache before
   evicting the least recently used entry. Default: ``10``.

``--client-timeout``, ``-ct`` *FLOAT*
   Seconds before a daemon client socket read or write times out. Prevents
   callers from hanging indefinitely when the daemon is slow or a circular
   ``credential_process`` reference causes a re-entrant request.
   Default: ``30.0``.

``--help``
   Show help message and exit.

Commands
--------

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - :ref:`config <elhaz-config>`
     - Manage elhaz configurations.
   * - :ref:`daemon <elhaz-daemon>`
     - Manage the elhaz daemon.
   * - :ref:`exec <elhaz-exec>`
     - Execute a one-off command with injected AWS credentials.
   * - :ref:`export <elhaz-export>`
     - Export credentials in multiple formats.
   * - :ref:`shell <elhaz-shell>`
     - Spawn an interactive shell with auto-refreshed credentials.
   * - :ref:`whoami <elhaz-whoami>`
     - Print the STS caller identity for a config.

Examples
--------

Override the config directory for all subcommands:

.. code-block:: bash

   elhaz --config-dir /custom/configs daemon start

Start the daemon with a custom socket path and a larger session cache:

.. code-block:: bash

   elhaz --socket-path /tmp/elhaz.sock --max-daemon-cache-size 20 daemon start
