# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.models."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from elhaz.models import (
    AssumeRoleModel,
    ConfigModel,
    CredentialProcessModel,
    ErrorModel,
    MFAModel,
    ProvidedContextModel,
    RequestModel,
    ResponseModel,
    SessionModel,
    STSModel,
    TagModel,
)

VALID_ROLE_ARN = "arn:aws:iam::123456789012:role/TestRole"


@pytest.mark.parametrize(
    "action",
    ["add", "credentials", "kill", "list", "remove", "whoami"],
)
def test_request_model_all_valid_actions(action: str) -> None:
    m = RequestModel(request_id=uuid4(), action=action)  # type: ignore[call-arg]
    assert m.action == action


def test_request_model_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError):
        RequestModel(request_id=uuid4(), action="explode")  # type: ignore[call-arg]


def test_request_model_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        RequestModel(request_id=uuid4(), action="list", unexpected_field="x")  # type: ignore[call-arg]


def test_request_model_default_version() -> None:
    m = RequestModel(request_id=uuid4(), action="list")
    assert m.version == 1


def test_request_model_default_payload_is_empty_dict() -> None:
    m = RequestModel(request_id=uuid4(), action="list")
    assert m.payload == {}


def test_request_model_requires_request_id() -> None:
    with pytest.raises(ValidationError):
        RequestModel(action="list")  # type: ignore[call-arg]


def test_request_model_custom_payload() -> None:
    m = RequestModel(
        request_id=uuid4(), action="add", payload={"config": "demo"}
    )
    assert m.payload == {"config": "demo"}


def test_response_model_ok_true_with_data() -> None:
    rid = uuid4()
    m = ResponseModel(request_id=rid, ok=True, data={"foo": "bar"})
    assert m.ok is True
    assert m.data == {"foo": "bar"}
    assert m.error is None


def test_response_model_ok_false_with_error() -> None:
    rid = uuid4()
    m = ResponseModel(
        request_id=rid,
        ok=False,
        error=ErrorModel(code=404, message="not found"),
    )
    assert m.ok is False
    assert m.error is not None
    assert m.error.code == 404
    assert m.data is None


def test_response_model_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ResponseModel(request_id=uuid4(), ok=True, surprise="oops")  # type: ignore[call-arg]


def test_response_model_default_version() -> None:
    m = ResponseModel(request_id=uuid4(), ok=True)
    assert m.version == 1


def test_error_model_valid() -> None:
    m = ErrorModel(code=400, message="bad request")
    assert m.code == 400
    assert m.message == "bad request"


def test_error_model_extra_forbidden() -> None:
    with pytest.raises(ValidationError):
        ErrorModel(code=500, message="oops", extra_field="x")  # type: ignore[call-arg]


def test_config_model_requires_assume_role() -> None:
    with pytest.raises(ValidationError):
        ConfigModel()  # type: ignore[call-arg]


def test_config_model_minimal() -> None:
    m = ConfigModel(AssumeRole=AssumeRoleModel(RoleArn=VALID_ROLE_ARN))
    assert m.AssumeRole.RoleArn == VALID_ROLE_ARN
    assert m.STS is None
    assert m.MFA is None
    assert m.Session is None


def test_config_model_with_all_optional_sections() -> None:
    m = ConfigModel(
        AssumeRole=AssumeRoleModel(RoleArn=VALID_ROLE_ARN),
        STS=STSModel(region_name="us-east-1"),
        MFA=MFAModel(command="oathtool"),
        Session=SessionModel(region_name="us-west-2"),
    )
    assert m.STS is not None
    assert m.MFA is not None
    assert m.Session is not None


def test_config_model_dump_exclude_none_drops_none_fields() -> None:
    m = ConfigModel(AssumeRole=AssumeRoleModel(RoleArn=VALID_ROLE_ARN))
    dumped = m.model_dump(exclude_none=True)
    assert "AssumeRole" in dumped
    assert "STS" not in dumped
    assert "MFA" not in dumped
    assert "Session" not in dumped


def test_assume_role_model_requires_role_arn() -> None:
    with pytest.raises(ValidationError):
        AssumeRoleModel()  # type: ignore[call-arg]


def test_assume_role_model_with_tags() -> None:
    m = AssumeRoleModel(
        RoleArn=VALID_ROLE_ARN,
        Tags=[TagModel(Key="env", Value="prod")],
    )
    assert m.Tags is not None
    assert len(m.Tags) == 1
    assert m.Tags[0].Key == "env"
    assert m.Tags[0].Value == "prod"


def test_assume_role_model_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        AssumeRoleModel(RoleArn=VALID_ROLE_ARN, Unknown="x")  # type: ignore[call-arg]


def test_assume_role_model_all_optional_none_by_default() -> None:
    m = AssumeRoleModel(RoleArn=VALID_ROLE_ARN)
    dumped = m.model_dump(exclude_none=True)
    assert list(dumped.keys()) == ["RoleArn"]


def test_assume_role_model_with_provided_contexts() -> None:
    m = AssumeRoleModel(
        RoleArn=VALID_ROLE_ARN,
        ProvidedContexts=[
            ProvidedContextModel(
                ProviderArn="arn:aws:iam::123456789012:oidc-provider/foo",
                ContextAssertion="ctx",
            )
        ],
    )
    assert m.ProvidedContexts is not None
    assert len(m.ProvidedContexts) == 1


def test_credential_process_model_default_version() -> None:
    m = CredentialProcessModel(
        AccessKeyId="AKIA",
        SecretAccessKey="secret",
        SessionToken="token",
        Expiration="2030-01-01T00:00:00Z",
    )
    assert m.Version == 1


def test_credential_process_model_all_fields() -> None:
    m = CredentialProcessModel(
        Version=1,
        AccessKeyId="AKID",
        SecretAccessKey="SAK",
        SessionToken="TOK",
        Expiration="2030-01-01T00:00:00Z",
    )
    assert m.AccessKeyId == "AKID"
    assert m.SecretAccessKey == "SAK"
    assert m.SessionToken == "TOK"
    assert m.Expiration == "2030-01-01T00:00:00Z"


def test_sts_model_all_optional() -> None:
    m = STSModel()
    assert m.region_name is None
    assert m.aws_access_key_id is None


def test_sts_model_with_region() -> None:
    m = STSModel(region_name="eu-west-1")
    assert m.region_name == "eu-west-1"


def test_sts_model_verify_can_be_bool_or_str() -> None:
    assert STSModel(verify=True).verify is True
    assert STSModel(verify="/path/to/ca.pem").verify == "/path/to/ca.pem"


def test_mfa_model_requires_command() -> None:
    with pytest.raises(ValidationError):
        MFAModel()  # type: ignore[call-arg]


def test_mfa_model_default_timeout() -> None:
    m = MFAModel(command="oathtool")
    assert m.timeout == 30


def test_mfa_model_command_can_be_list() -> None:
    m = MFAModel(command=["oathtool", "--totp", "SECRET"])
    assert isinstance(m.command, list)


def test_session_model_all_optional() -> None:
    m = SessionModel()
    dumped = m.model_dump(exclude_none=True)
    assert dumped == {}


def test_session_model_with_region() -> None:
    m = SessionModel(region_name="ap-southeast-1")
    assert m.region_name == "ap-southeast-1"


def test_tag_model_valid() -> None:
    m = TagModel(Key="CostCenter", Value="9999")
    assert m.Key == "CostCenter"
    assert m.Value == "9999"


def test_tag_model_requires_both_fields() -> None:
    with pytest.raises(ValidationError):
        TagModel(Key="only-key")  # type: ignore[call-arg]


def test_provided_context_model_valid() -> None:
    m = ProvidedContextModel(
        ProviderArn="arn:aws:iam::123:oidc-provider/foo",
        ContextAssertion="assertion-value",
    )
    assert m.ProviderArn.startswith("arn:")
    assert m.ContextAssertion == "assertion-value"


def test_provided_context_model_requires_both_fields() -> None:
    with pytest.raises(ValidationError):
        ProvidedContextModel(ProviderArn="arn:x")  # type: ignore[call-arg]
