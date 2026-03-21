.. _config:

Config
======

In order to initialize and cache AWS sessions which automatically refresh temporary AWS credentials, elhaz uses `boto3-refresh-session <https://github.com/61418/boto3-refresh-session>`_ as a dependency.

In order to configure those AWS sessions with elhaz, you must set up configs which represent sets of parameters for :class:`boto3_refresh_session.methods.sts.STSRefreshableSession`.
These configs are stored by default in ``~/.elhaz/configs/`` as YAML files.

There are two methods for creating configs:

1. Manually by hand (not recommended)
2. Using ``elhaz config add`` (recommended)

**It is highly recommended to use the second method**.

``elhaz config add`` provides interactive prompts for creating configs.
elhaz verifies data types, but it does not verify the *correctness* of data (e.g. whether a provided ARN is valid or not).

There are four categories of parameters for configs, which you may explore below.

.. toctree::
   :maxdepth: 1

    AssumeRole <assumerole>
    STS <sts>
    MFA <mfa>
    Session <session>

.. attention::

   The only required parameter for configs is ``RoleArn`` in the ``AssumeRole`` category.

A fully configured config -- that is, a config which includes all required and optional parameters -- would look like this:

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
    MFA:
      command: str
      timeout: int
    Session:
      region_name: str
      profile_name: str
      aws_account_id: str
      aws_access_key_id: str
      aws_secret_access_key: str
      aws_session_token: str                      