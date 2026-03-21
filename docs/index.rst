elhaz
=====

**Version:** |release|

**License:** `Mozilla Public License 2.0 <https://github.com/michaelthomasletts/elhaz/blob/main/LICENSE>`_

**Author:** `Mike Letts <https://michaelthomasletts.com>`_

**Maintainers:** `61418 <https://61418.io>`_

Description
-----------

elhaz is a CLI tool and daemon for managing automatically refreshed temporary
AWS credentials via `boto3-refresh-session <https://github.com/61418/boto3-refresh-session>`_.

It exposes credentials to shells, SDKs, CLIs, scripts, and other tools using
a UNIX domain socket with an in-memory session cache and a threaded refresh
loop.

Why this Exists
---------------

Temporary AWS credentials expire.
Managing that expiration manually — or delegating it to individual tools —
leads to redundant session creation, repeated STS calls, and credentials that
silently expire mid-task.

elhaz solves this by running a single, long-lived daemon process on your local
machine.
The daemon holds a bounded LRU cache of active AWS sessions, each backed by
`boto3-refresh-session <https://github.com/61418/boto3-refresh-session>`_,
which automatically refreshes credentials before they expire.
The CLI acts as the control plane: starting and stopping the daemon, adding
and removing sessions, and retrieving credentials in multiple formats.

This means:

- Credentials refresh silently in the background.
- Multiple IAM roles can be active simultaneously.
- Any shell, SDK, script, or tool can consume credentials without knowing
  about the daemon.

Design
------

elhaz separates concerns into three layers:

- **Config**: Named YAML files stored in ``~/.elhaz/configs/``, each
  representing the parameters needed to initialize an AWS session via
  boto3-refresh-session.
- **Daemon**: A background process that holds a bounded LRU cache of active
  sessions and serves credential requests over a UNIX domain socket.
- **CLI**: A Typer-based command-line interface that acts as the control plane
  for the daemon and a consumer of its credentials.

Communication between the CLI and the daemon uses a simple JSON
request/response protocol over the socket — one request per connection.

.. toctree::
   :maxdepth: 1
   :caption: Sitemap
   :name: sitemap
   :hidden:

   CLI <cli/index>
   Concepts <concepts/index>
   Installation <installation>
   Quickstart <quickstart>