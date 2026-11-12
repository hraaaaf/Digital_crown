"""RequestValidationError with a nested Pydantic ValueError must remain 422.

This is a pure synthetic regression for FastAPI's shared JSON error adapter.
It does not alter clinical payloads, schema validation or authorization.
"""
import asyncio
import json

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

from backend.main import validation_exception_handler


def _response(errors):
    request = Request({
        "type": "http", "method": "POST",
        "path": "/api/ia/analyses/901/calibrate", "headers": [],
        "query_string": b"",
    })
    exception = RequestValidationError(errors)
    return asyncio.run(validation_exception_handler(request, exception))


def test_pydantic_calibration_value_error_is_safe_422_not_internal_500():
    response = _response([{
        "type": "value_error",
        "loc": ("body", "distance_mm"),
        "msg": "Value error, La distance doit etre positive",
        "input": -1,
        "ctx": {"error": ValueError("La distance doit etre positive")},
    }])
    assert response.status_code == 422
    assert response.media_type == "application/json"
    payload = json.loads(response.body)
    assert len(payload["detail"]) == 1
    field = payload["detail"][0]
    assert field["loc"] == ["body", "distance_mm"]
    assert field["msg"] == "Value error, La distance doit etre positive"
    assert field["input"] == -1
    assert "Traceback" not in response.body.decode()


def test_regular_request_validation_error_keeps_422_contract():
    response = _response([{
        "type": "int_parsing", "loc": ("path", "analysis_id"),
        "msg": "Input should be a valid integer", "input": "invalid",
    }])
    assert response.status_code == 422
    payload = json.loads(response.body)
    assert payload["detail"][0]["type"] == "int_parsing"
    assert payload["detail"][0]["loc"] == ["path", "analysis_id"]
