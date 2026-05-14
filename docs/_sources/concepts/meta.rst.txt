.. _meta:

Meta
====

.. tip::

    The ``Meta`` object is completely optional in a config.

The ``Meta`` object stores human-readable metadata *about* a config.
It exists purely for your reference and has **no effect** on how elhaz
initializes an AWS session — its fields are never forwarded to
:class:`boto3_refresh_session.methods.sts.STSRefreshableSession` or any
underlying boto3/STS call.

When to use ``Meta``
--------------------

Use ``Meta`` whenever you want to leave a note explaining what a config is
for — for example, which team owns the role, what environment it targets, or
why a particular ``DurationSeconds`` was chosen.

Parameters
----------

``description``
    A free-form string describing the config.

.. code-block:: yaml

    Meta:
      description: str

Example
-------

.. code-block:: yaml

    AssumeRole:
      RoleArn: arn:aws:iam::012345678901:role/your-role
    Meta:
      description: Production read-only role for the data-platform team.

Adding metadata interactively
------------------------------

When running :ref:`elhaz config add <elhaz-config-add>` or
:ref:`elhaz config update <elhaz-config-update>`, you will be asked:

.. code-block:: text

    Add a description to this config? (y/N)

Answer ``y`` to enter a description; answer ``n`` (or press Enter) to skip.

Viewing metadata
----------------

Use :ref:`elhaz config meta <elhaz-config-meta>` to print the ``Meta``
section of an existing config:

.. code-block:: console

    $ elhaz config meta --name my-config
    {
      "description": "Production read-only role for the data-platform team."
    }
