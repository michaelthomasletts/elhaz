elhaz
=====

**Version:** |release|

**License:** `Mozilla Public License 2.0 <https://github.com/michaelthomasletts/elhaz/blob/main/LICENSE>`_

**Author:** `Mike Letts <https://michaelthomasletts.com>`_

**Maintainers:** `61418 <https://61418.io>`_

What is elhaz?
--------------

elhaz is a local daemon-backed AWS temporary credential broker, exposed over a Unix socket and controlled via CLI.

Instead of a locally hosted HTTP metadata emulation service (ECS), which is less secure and requires multiple processes for each assumed RoleArn, elhaz runs a single process and serves automatically refreshed temporary AWS credentials on demand. 

elhaz caches AWS sessions for however long the daemon is kept alive (or sessions are removed by command), which eliminates redundant session creations and STS calls. 

Unix-socket IPC is lightweight and gives a tighter local boundary than HTTP, avoids exposing local credential endpoints over TCP, and allows temporary credentials to live in memory rather than at rest on disk.

**elhaz makes multi-role local AWS workflows cleaner by combining brokered access, in-memory caching, and host-local IPC into one model.**

How do I use elhaz?
-------------------

To install this tool, check the :ref:`installation <installation>` guide.

To get started quickly, check the :ref:`quickstart <quickstart>` guide.

To learn critical concepts for using this tool, check the :ref:`concepts <concepts>` section of the docs.

For technical details, check the :ref:`CLI docs <cli>`.

How did elhaz get its name?
---------------------------

Initially, the intention was to name this project "assume".
However, that namespace was already taken and, frankly, "assume" seems a little trite, derivative, and *on-the-nose*. 

The algriz rune (also called "elhaz") is the 15th letter of the Elder Futhark alphabet. 
It symbolizes *protection and defense*, among other related themes and concepts which befit a local credential broker. 

"elhaz" is *pithy*. 
Ideally, a CLI tool ought to have a *memorable and compact* name. 

.. toctree::
   :maxdepth: 1
   :caption: Sitemap
   :name: sitemap
   :hidden:

   CLI <cli/index>
   Concepts <concepts/index>
   Installation <installation>
   Quickstart <quickstart>