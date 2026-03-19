# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

__all__ = [
    "BaseElhazError",
    "ElhazAlreadyExistsError",
    "ElhazBadRequestError",
    "ElhazDaemonError",
    "ElhazNotFoundError",
    "ElhazValidationError",
]

from typing import Any, Dict


class BaseElhazError(Exception):
    """The base exception for elhaz."""

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | int | None = None,
        status_code: int | None = None,
        details: Dict[str, Any] | None = None,
        param: str | None = None,
        value: Any | None = None,
    ) -> None:
        self.message = "" if message is None else message
        self.code = code
        self.status_code = status_code
        self.details = details
        self.param = param
        self.value = value
        super().__init__(self.message)

    def __str__(self) -> str:
        base = self.message
        extras: list[str] = []
        if self.code is not None:
            extras.append(f"code={self.code!r}")
        if self.status_code is not None:
            extras.append(f"status_code={self.status_code!r}")
        if self.param is not None:
            extras.append(f"param={self.param!r}")
        if self.value is not None:
            extras.append(f"value={self.value!r}")
        if self.details is not None:
            extras.append(f"details={self.details!r}")
        if extras:
            if base:
                return f"{base} ({', '.join(extras)})"
            return ", ".join(extras)
        return base

    def __repr__(self) -> str:
        args = [repr(self.message)]
        if self.code is not None:
            args.append(f"code={self.code!r}")
        if self.status_code is not None:
            args.append(f"status_code={self.status_code!r}")
        if self.param is not None:
            args.append(f"param={self.param!r}")
        if self.value is not None:
            args.append(f"value={self.value!r}")
        if self.details is not None:
            args.append(f"details={self.details!r}")
        return f"{self.__class__.__name__}({', '.join(args)})"


class ElhazNotFoundError(BaseElhazError):
    """Raised when a requested object is not found."""


class ElhazAlreadyExistsError(BaseElhazError):
    """Raised when an object already exists."""


class ElhazBadRequestError(BaseElhazError):
    """Raised when a request is invalid."""


class ElhazValidationError(BaseElhazError):
    """Raised when validation of input data fails."""


class ElhazDaemonError(BaseElhazError):
    """Raised when there is an error in the elhaz daemon."""


# Backward-compatible aliases for the former project name.
BaseAssumeError = BaseElhazError
AssumeNotFoundError = ElhazNotFoundError
AssumeAlreadyExistsError = ElhazAlreadyExistsError
AssumeBadRequestError = ElhazBadRequestError
AssumeValidationError = ElhazValidationError
AssumeDaemonError = ElhazDaemonError
