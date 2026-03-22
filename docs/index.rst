elhaz
=====

**Version:** |release|

**License:** `Mozilla Public License 2.0 <https://github.com/michaelthomasletts/elhaz/blob/main/LICENSE>`_

**Author:** `Mike Letts <https://michaelthomasletts.com>`_

**Maintainers:** `61418 <https://61418.io>`_

What is elhaz?
--------------

ᛉ elhaz ᛉ is a local AWS credential broker daemon exposed over a Unix socket.

Instead of a locally hosted HTTP metadata emulation service (ECS), which requires multiple processes for each assumed RoleArn, elhaz runs a single process (which accepts multiple concurrent connections) and serves automatically refreshed temporary AWS credentials on demand. 

It caches AWS sessions for however long the daemon is kept alive, which eliminates redundant session creations and STS calls. 

Unix-socket IPC is lightweight and gives a tighter local boundary than HTTP, avoids exposing local credential endpoints over TCP, and allows temporary credentials to live in memory rather than at rest on disk.

elhaz makes multi-role local AWS workflows cleaner by combining brokered access, in-memory caching, and host-local IPC in one model.

.. toctree::
   :maxdepth: 1
   :caption: Sitemap
   :name: sitemap
   :hidden:

   CLI <cli/index>
   Concepts <concepts/index>
   Installation <installation>
   Quickstart <quickstart>