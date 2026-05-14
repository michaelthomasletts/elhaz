.. _mfa:

MFA
===

.. tip::

    The ``MFA`` object is completely optional in a config.

The ``MFA`` object in a config represents parameters for initializing :class:`boto3_refresh_session.methods.sts.STSRefreshableSession`.

``MFA`` can accept the following parameters in your config file:

.. code-block:: yaml

    MFA:
      command: str
      timeout: int

The ``command`` parameter is a string that represents a CLI command to retrieve an MFA token code. 
The command should output *only* the MFA token code as a string to stdout.
:class:`boto3_refresh_session.methods.sts.STSRefreshableSession` will execute the command and use the output as the MFA token code when refreshing temporary credentials.

The ``timeout`` parameter is an integer that represents the number of seconds to wait for the command to execute before timing out.
The default value for ``timeout`` is 30 seconds.