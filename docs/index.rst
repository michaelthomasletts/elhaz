elhaz
=====

**Version:** |release|

**License:** `Mozilla Public License 2.0 <https://github.com/michaelthomasletts/elhaz/blob/main/LICENSE>`_

**Author:** `Mike Letts <https://michaelthomasletts.com>`_

**Maintainers:** `61418 <https://61418.io>`_

Description
-----------

elhaz provides a local credential management system for AWS temporary credentials.

It maintains a bounded, refreshable cache of AWS sessions, each corresponding to a named configuration, and exposes those credentials to shells, SDKs, CLIs, and other tools.
A long-lived daemon process coordinates session lifecycle, refresh, and retrieval across local consumers.


Why this Exists
---------------

Temporary AWS credentials expire.

Managing that expiration locally — whether through ``credential_process``, environment variables, or tool-specific behavior — often leads to repeated session creation, redundant STS calls, and credentials that expire at inconvenient times.

AWS provides primitives for credential retrieval and refresh.
However, these mechanisms operate at the level of individual processes and do not coordinate credential reuse across a local environment.

As a result:

- The same role may be assumed multiple times across different processes
- Credential refresh occurs independently per tool
- Session lifecycles are fragmented and difficult to reason about

elhaz introduces a single, local coordination layer for temporary credentials.

Each configuration corresponds to one session, which is:

- Initialized once
- Reused across processes
- Refreshed automatically before expiration

This ensures credential retrieval is consistent, efficient, and predictable.


Design
------

elhaz separates credential management into three components:

- **Config**: Named YAML configurations stored in ``~/.elhaz/configs/``, defining how sessions are initialized
- **Daemon**: A local process maintaining a bounded LRU cache of active sessions
- **CLI**: A command-line interface for interacting with configurations and retrieving credentials

Each session is backed by `boto3-refresh-session <https://github.com/61418/boto3-refresh-session>`_, which provides automatic credential refresh.

The daemon enforces:

- One session per configuration
- Bounded cache size with LRU eviction
- Centralized refresh and lifecycle management

Communication between the CLI and daemon occurs over a UNIX domain socket using a request/response protocol.

These design decisions reflect the core goals of elhaz:

- **Deterministic session reuse**
- **Centralized credential lifecycle management**
- **Reduced redundant STS calls**
- **Consistent behavior across local tools**

.. toctree::
   :maxdepth: 1
   :caption: Sitemap
   :name: sitemap
   :hidden:

   CLI <cli/index>
   Concepts <concepts/index>
   Installation <installation>
   Quickstart <quickstart>