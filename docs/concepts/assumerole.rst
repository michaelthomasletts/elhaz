.. _assumerole:

AssumeRole
==========

.. tip::

    The only required parameter for the ``AssumeRole`` object is ``RoleArn``.
    All other parameters are completely optional.
  
.. warning:: 

    Although you *may* provide ``TokenCode`` for MFA, **this is not recommended**.
    You will need to edit your config every time your MFA token changes, which is roughly every 30 seconds.
    Instead, provide a CLI command for your token provider to the ``command`` parameter in the :ref:`MFA <mfa>` object.
    :class:`boto3_refresh_session.methods.sts.STSRefreshableSession` will automatically call your token provider command and use the output from stdout as the MFA token when needed.

The ``AssumeRole`` object in a config represents parameters for :meth:`STS.Client.assume_role`.

``AssumeRole`` can accept the following parameters in your config file:

.. code-block:: yaml

    AssumeRole:
      RoleArn: str
      RoleSessionName: str
      ExternalId: str
      SerialNumber: str
      TokenCode: str
      SourceIdentity: str
      Policy: str
      PolicyArns:
        - str
      Tags:
        - Key: str
          Value: str
      TransitiveTagKeys:
        - str
      ProvidedContexts:
        - ProviderArn: str
          ContextAssertion: str