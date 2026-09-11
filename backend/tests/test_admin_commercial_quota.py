def test_elite_dashboard_exposes_semantic_unlimited_without_upgrade_warning(
    client, db, auth_headers, dentiste
):
    dentiste.subscription_plan = "ELITE"
    db.commit()

    response = client.get("/api/admin/dashboard/stats", headers=auth_headers)

    assert response.status_code == 200
    quota = response.json()["team_quota"]
    assert quota is not None
    assert quota["plan"] == "ELITE"
    assert quota["dentistes_max"] is None
    assert quota["secretaires_max"] is None
    assert quota["upgrade_required"] is False
