"""Pydantic models for boto3-refresh-session configuration."""

__all__ = [
    "AssumeRoleModel",
    "ConfigModel",
    "MFAModel",
    "SessionModel",
    "STSModel",
]

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, model_validator

from .exceptions import AssumeValidationError

actions = Literal["add", "credentials", "list", "remove", "whoami"]


class _BaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TagModel(_BaseModel):
    """Model for AWS STS session tags."""

    Key: str
    Value: str


class ProvidedContextModel(_BaseModel):
    """Model for AWS STS provided contexts."""

    ProviderArn: str
    ContextAssertion: str


class AssumeRoleModel(_BaseModel):
    """Model for AWS STS AssumeRole parameters."""

    RoleArn: str
    RoleSessionName: Optional[str] = None
    PolicyArns: Optional[list[str]] = None
    Policy: Optional[str] = None
    DurationSeconds: Optional[int] = None
    ExternalId: Optional[str] = None
    SerialNumber: Optional[str] = None
    TokenCode: Optional[str] = None
    Tags: Optional[list[TagModel]] = None
    TransitiveTagKeys: Optional[list[str]] = None
    SourceIdentity: Optional[str] = None
    ProvidedContexts: Optional[list[ProvidedContextModel]] = None


class STSModel(_BaseModel):
    """Model for AWS STS client parameters."""

    region_name: Optional[str] = None
    api_version: Optional[str] = None
    use_ssl: Optional[bool] = None
    verify: Optional[bool | str] = None
    endpoint_url: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    aws_account_id: Optional[str] = None


class MFAModel(_BaseModel):
    """Model for AWS STS MFA parameters."""

    command: str | list[str]
    timeout: Optional[int] = 30


class SessionModel(_BaseModel):
    """Model for AWS STS session parameters."""

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    region_name: Optional[str] = None
    profile_name: Optional[str] = None
    aws_account_id: Optional[str] = None


class ConfigModel(_BaseModel):
    """Model for boto3-refresh-session configuration."""

    AssumeRole: AssumeRoleModel
    STS: Optional[STSModel] = None
    MFA: Optional[MFAModel] = None
    Session: Optional[SessionModel] = None


class RequestModel(_BaseModel):
    """Model for requests sent to the daemon."""

    action: actions
    config: Optional[str] = None

    @model_validator(mode="after")
    def validate_config_requirement(self):
        if self.action not in ("kill", "list") and self.config is None:
            raise AssumeValidationError(
                f"'config' is required for action '{self.action}'"
            )
        return self
