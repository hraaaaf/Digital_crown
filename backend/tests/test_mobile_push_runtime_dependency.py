import importlib


def test_mobile_push_runtime_dependency_available():
    module = importlib.import_module("backend.services.mobile_push_service")
    assert callable(module.webpush)
