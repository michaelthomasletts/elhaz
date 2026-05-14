.. _identitycenter:

IAM Identity Center (SSO)
=========================

Does elhaz support AWS IAM Identity Center (SSO)?
-------------------------------------------------

In most cases, yes.

elhaz uses boto3-refresh-session as its core dependency for refreshing temporary AWS security credentials.
boto3-refresh-session depends on botocore, which in turn has support for AWS IAM Identity Center (SSO).
Thus, elhaz supports AWS IAM Identity Center (SSO).

elhaz (and boto3-refresh-session) does not reinvent the wheel when it comes to SSO support.
elhaz does not, in other words, have an ``sso login`` command built-in. 
Rather, elhaz leverages AWS-native support (in botocore) for acquiring temporary credentials via IAM Identity Center (SSO).
Accordingly, the usual steps for configuring and logging into IAM Identity Center (SSO) via the AWS CLI apply here.

Who can use elhaz with IAM Identity Center (SSO)?
-------------------------------------------------

Organizations with standard authentication setups that employ IAM Identity Center (SSO) in tandem with tools like Okta or Google Workspace will find elhaz helpful and easy to use.

Organizations with highly complex, idiosyncratic, and-or non-standard authentication setups (such as ConsoleMe/Weep at Netflix), however, *may* not find elhaz useful or usable.
It depends.
AWS authentication setups vary widely across organizations.
It is **highly recommended** therefore that you carefully evaluate your organization's specific authentication setup to determine whether elhaz can integrate with it effectively, if at all.
If you are unsure if your organization's authentication setup can work with elhaz, open an issue on the elhaz GitHub repository so that the maintainers can help you assess compatibility.

.. warning::

    boto3-refresh-session only supports ``AssumeRole``.
    It does not support ``AssumeRoleWithSAML`` or ``AssumeRoleWithWebIdentity``.
    When working with roles that are assumed via ``AssumeRoleWithSAML`` or ``AssumeRoleWithWebIdentity``, boto3-refresh-session (and therefore elhaz) will not be able to acquire temporary credentials for those specific roles.
    In the future, boto3-refresh-session may add support for ``AssumeRoleWithSAML`` and ``AssumeRoleWithWebIdentity``.

How do I use elhaz with IAM Identity Center (SSO)?
--------------------------------------------------

Honestly, if you already know how to configure and log into IAM Identity Center (SSO) via the AWS CLI then using elhaz with SSO is straightforward.

Locally configure IAM Identity Center (SSO) using the AWS CLI, if you haven't done so already, like you normally would using the AWS CLI.

.. code-block:: bash

    aws configure sso

Next, log in to the AWS SSO session so that elhaz (via boto3-refresh-session / botocore) can pick up the temporary credentials that were established by the SSO login.

.. code-block:: bash

    aws sso login

Now that the SSO session has been established via the AWS CLI login, elhaz can be used to acquire temporary credentials for assumed roles that are authenticated via IAM Identity Center (SSO) in the same manner as it would for other credential sources.

Don't forget to logout! 

.. code-block:: bash

    aws sso logout