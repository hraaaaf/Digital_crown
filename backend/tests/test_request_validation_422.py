"""Synthetic ASGI regression for Pydantic's non-JSON-serializable error context.

The Cabinet response must be an ordinary HTTP 422, never an unhandled 500.
No clinical records, media, real patients, DB, model, or secrets are used.
"""
import logging

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator

from backend.main import validation_exception_handler


class _SyntheticScale(BaseModel):
    distance_mm: float

    @field_validator("distance_mm")
    @classmethod
    def require_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("La distance doit etre positive")
        return value


def _client():
    app = FastAPI()
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.post("/synthetic-calibration-validation")
    def verify_scale(payload: _SyntheticScale):
        return {"distance_mm": payload.distance_mm}

    return TestClient(app)


@pytest.mark.parametrize(
    "invalid_value,error_type",
    [
        (-1, "value_error"),  # Pydantic ctx.error contains a real ValueError.
        ("SYNTHETIC_PRIVATE_INPUT_MARKER", "float_parsing"),
    ],
)
def test_validation_handler_returns_json_422_without_exposing_raw_input_in_logs(
    caplog, invalid_value, error_type
):
    with caplog.at_level(logging.WARNING), _client() as client:
        response = client.post(
            "/synthetic-calibration-validation",
            json={"distance_mm": invalid_value},
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0]["loc"] == ["body", "distance_mm"]
    assert detail[0]["type"] == error_type
    assert isinstance(detail[0]["msg"], str)
    # A ValueError object inside ctx must not trigger a secondary 500.
    if error_type == "value_error":
        assert isinstance(detail[0]["ctx"]["error"], dict)
    assert "SYNTHETIC_PRIVATE_INPUT_MARKER" not in caplog.text
    assert "Validation Error:" not in caplog.text


def test_positive_distance_is_unchanged():
    with _client() as client:
        response = client.post(
            "/synthetic-calibration-validation", json={"distance_mm": 20}
        )
    assert response.status_code == 200
    assert response.json() == {"distance_mm": 20.0}
