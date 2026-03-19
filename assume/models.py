"""Pydantic models for boto3-refresh-session configuration."""

__all__ = [
    "AssumeRoleModel",
    "ConfigModel",
    "ErrorModel",
    "MFAModel",
    "RequestModel",
    "ResponseModel",
    "SessionModel",
    "STSModel",
]

from typing import Any, Dict, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

actions = Literal["add", "credentials", "kill", "list", "remove", "whoami"]


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


class ErrorModel(_BaseModel):
    """Model for structured daemon error responses.

    Attributes
    ----------
    code : int
        Numeric error code (HTTP-like: 400, 404, 409, 500).
    message : str
        Human-readable description of the error.
    """

    code: int
    message: str


class RequestModel(_BaseModel):
    """Model for requests sent to the daemon.

    Attributes
    ----------
    version : int
        Protocol version. Defaults to 1.
    request_id : UUID
        Client-generated unique identifier echoed back in the response.
    action : str
        The daemon action to invoke.
    payload : dict[str, Any]
        Action-specific fields. Defaults to an empty dict.
    """

    version: int = 1
    request_id: UUID
    action: actions
    payload: Dict[str, Any] = {}


class ResponseModel(_BaseModel):
    """Model for responses sent by the daemon.

    Either ``data`` or ``error`` is populated, never both.

    Attributes
    ----------
    version : int
        Protocol version. Defaults to 1.
    request_id : UUID
        Echoed from the originating request.
    ok : bool
        True on success, False on error.
    data : Any, optional
        Action-specific result payload. Present when ``ok`` is True.
    error : ErrorModel, optional
        Structured error detail. Present when ``ok`` is False.
    """

    version: int = 1
    request_id: UUID
    ok: bool
    data: Any = None
    error: Optional[ErrorModel] = None
