.. _daemon:

Daemon
======

What does the daemon do?
------------------------

elhaz uses a daemon process to manage temporary AWS credentials.
The daemon is responsible for initializing and caching AWS sessions (in a bounded LRU cache), refreshing temporary AWS credentials, and providing credentials to the CLI when requested.

To do this, elhaz uses a **Unix domain socket** for local IPC between the CLI and the daemon.

The daemon enables a single, long-lived credential authority on the local machine. 
Instead of redundantly creating new sessions or calling AWS STS from *multiple processes*, elhaz reuses existing sessions (which are configured by :ref:`config <config>` objects) and refreshes them in the background using boto3-refresh-session within a *single process*.

This provides:

- Enhanced security via Unix socket permissions and local-only access
- Multiple role assumptions without redundant session creation or STS calls
- Consistent credential reuse
- Immediate access to valid credentials
- Centralized lifecycle management for temporary sessions

Why not locally hosted HTTP for ECS metadata service emulation?
---------------------------------------------------------------

The AWS CLI allows ECS metadata emulation via a locally hosted HTTP endpoint, configured using ``AWS_CONTAINER_CREDENTIALS_FULL_URI``.
This technique is native to the AWS ecosystem and is used by many popular tools to provide credentials to SDKs and other tools.

However, this approach has some tradeoffs for a local developer tool:

- HTTP server complexity/weight
- Optional TLS and authorization concerns
- Increased surface area for local networking and configuration
- Managing multiple endpoints or routing logic for multiple assumed roles

In contrast, elhaz uses a Unix domain socket, which is:

- Local-only by design (no network exposure)
- Simpler to implement and reason about
- Well-suited for single-machine coordination
- Naturally aligned with CLI-driven workflows

For local development, where both the CLI and daemon run on the same machine, a Unix domain socket provides a minimal and efficient communication mechanism without requiring HTTP semantics.

A direct quote from Lachlan Donald, founder of aws-vault:

    *"IMO a unix socket is vastly better."*

How do I start the daemon?
--------------------------

First, you need to have :ref:`at least one config created <elhaz-config-add>`. 

After that condition is satisfied, check the docs for :ref:`elhaz daemon start <elhaz-daemon-start>`.

How do I stop the daemon?
-------------------------

Check the docs for :ref:`elhaz daemon stop <elhaz-daemon-stop>`.

How do I read the logs from the daemon?
---------------------------------------

Check the docs for :ref:`elhaz daemon logs <elhaz-daemon-logs>`.

How do I add a config to the daemon?
------------------------------------

Good catch. 
In order for the daemon to manage credentials for a config, that config must be added to the daemon's cache.
To do that, check the docs for :ref:`elhaz config add <elhaz-config-add>`.

How do I remove a config from the daemon?
-----------------------------------------

Check the docs for :ref:`elhaz config remove <elhaz-config-remove>`.