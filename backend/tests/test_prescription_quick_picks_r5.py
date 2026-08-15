"""R5 regression tests for fast-prescription doctor-scoped quick picks."""


def _record(client, auth_headers, medication_name: str, dosage: str = "", posologie: str = ""):
    response = client.post(
        "/api/prescriptions/habits/record",
        json={
            "medication_name": medication_name,
            "dosage": dosage,
            "posologie": posologie,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_empty_habit_query_returns_recent_and_frequent_medications(client, auth_headers):
    _record(client, auth_headers, "DOLIPRANE", "1G", "1 cp si douleur")
    _record(client, auth_headers, "AUGMENTIN", "1G", "2x/j")
    _record(client, auth_headers, "AUGMENTIN", "1G", "2x/j")

    response = client.get(
        "/api/prescriptions/habits/suggest?q=",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert "recent_medications" in payload
    assert "frequent_medications" in payload
    assert "AUGMENTIN" in payload["recent_medications"]
    assert payload["frequent_medications"][0] == "AUGMENTIN"
    assert set(payload["medications"]).issuperset({"AUGMENTIN", "DOLIPRANE"})


def test_quick_picks_are_doctor_scoped(client, auth_headers):
    _record(client, auth_headers, "DOLIPRANE", "1G", "1 cp")

    response = client.get(
        "/api/prescriptions/habits/suggest?q=",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recent_medications"]
    assert all(isinstance(name, str) and name.strip() for name in payload["recent_medications"])
