.. _config:

Config
======

What is a config?
-----------------

A config in elhaz is **not the same thing** as the local config file for AWS profiles (i.e. ``~/.aws/config``).

Rather, a config in elhaz represents a static configuration file (stored by default in ``~/.elhaz/configs`` as a YAML file) for initializing a :class:`boto3_refresh_session.methods.sts.STSRefreshableSession` object. 
elhaz uses boto3-refresh-session as a dependency specifically to initialize and cache AWS sessions which automatically refresh temporary AWS credentials from elhaz's daemon. 
Ideally, config creation should be a one-time investment in order to avoid drift.

Each config has a unique namespace. Although two config objects may have identical configurations, they cannot share the same config name. 

What does a config contain?
---------------------------

A valid config can contain five objects:

.. toctree::
   :maxdepth: 1

    AssumeRole <assumerole>
    STS <sts>
    MFA <mfa>
    Session <session>
    Meta <meta>

It is **HIGHLY RECOMMENDED** to read through each section above in order to learn more about properly configuring these objects and their respective parameters.

The **only required object** in a config is :ref:`assumerole`, specifically the ``RoleArn`` parameter for the :ref:`assumerole` object.

Accordingly, **a minimally viable config** file looks like this:

.. code-block:: yaml

  AssumeRole:
      RoleArn: arn:aws:iam::012345678901:role/your-role

However, **a fully populated** config file is structured like this:

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
  Meta:
    description: str

How do I create a config?
-------------------------

Check the docs for :ref:`elhaz config add <elhaz-config-add>`.

How do I edit an existing config?
---------------------------------

Check the docs for :ref:`elhaz config update <elhaz-config-update>`.

How do I remove an existing config?
-------------------------------------

Check the docs for :ref:`elhaz config remove <elhaz-config-remove>`.

How do I inspect an existing config?
----------------------------------------

Check the docs for :ref:`elhaz config get <elhaz-config-get>`.

How do I list all existing configs?
---------------------------------------

Check the docs for :ref:`elhaz config list <elhaz-config-list>`.

How do I view the metadata for an existing config?
---------------------------------------------------

Check the docs for :ref:`elhaz config meta <elhaz-config-meta>`.