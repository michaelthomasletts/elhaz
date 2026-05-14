.. _sts:

STS
===

.. tip::

    The ``STS`` object is completely optional in a config.

.. warning::

    It is not recommended to provide ``aws_access_key_id``, ``aws_secret_access_key``, or ``aws_session_token`` in the ``STS`` object of your config!
    These parameters are only provided for interoperability with AWS.

The ``STS`` object in a config represents parameters for :class:`STS.Client`.

``STS`` can accept the following parameters in your config file:

.. code-block:: yaml

    STS:
      region_name: str
      api_version: str
      use_ssl: bool
      verify: bool
      endpoint_url: str
      aws_access_key_id: str
      aws_secret_access_key: str
      aws_session_token: str
      aws_account_id: str