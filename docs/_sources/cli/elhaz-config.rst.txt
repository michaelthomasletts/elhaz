.. _elhaz-config:

``elhaz config``
================

Synopsis
--------

.. code-block:: text

   elhaz config COMMAND [ARGS]...

Description
-----------

Manage elhaz configurations. Configs are named YAML files stored in
``~/.elhaz/configs/`` (or the directory set by ``--config-dir``). Each config
holds the parameters needed to initialize an automatically refreshed AWS
session via `boto3-refresh-session <https://github.com/61418/boto3-refresh-session>`_.

Options
-------

``--help``
   Show help message and exit.

Commands
--------

.. list-table::
   :widths: 30 70
   :header-rows: 0

   * - :ref:`add <elhaz-config-add>`
     - Create a new config.
   * - :ref:`get <elhaz-config-get>`
     - Display a config as formatted JSON.
   * - :ref:`list <elhaz-config-list>`
     - List all config names.
   * - :ref:`meta <elhaz-config-meta>`
     - Print the metadata for a config.
   * - :ref:`remove <elhaz-config-remove>`
     - Delete a config.
   * - :ref:`update <elhaz-config-update>`
     - Update a config interactively.

.. toctree::
   :hidden:

   elhaz config add <elhaz-config-add>
   elhaz config get <elhaz-config-get>
   elhaz config list <elhaz-config-list>
   elhaz config meta <elhaz-config-meta>
   elhaz config remove <elhaz-config-remove>
   elhaz config update <elhaz-config-update>
