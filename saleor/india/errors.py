from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ValidationError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


@dataclass(slots=True)
class PaymentGatewayError(Exception):
    message: str
    code: str | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.message


