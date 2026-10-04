import math, pytest
from scripts.validate_cephalo_vnext_lot02_g0 import (
    EXPECTED,FIXTURE,G0Error,acute_line_angle,compute_fixture,distance_mm,vertex_angle,
)

def test_g0_exact_geometry_fixture():
    got=compute_fixture()
    assert set(got)==set(EXPECTED)
    for key,value in EXPECTED.items():
        assert got[key]==pytest.approx(value,abs=1e-12)

def test_g0_degenerate_geometry_fails_closed():
    with pytest.raises(G0Error):
        vertex_angle((0,0),(0,0),(1,1))
    with pytest.raises(G0Error):
        acute_line_angle((0,0),(0,0),(1,1),(2,2))
    with pytest.raises(G0Error):
        distance_mm((0,0),(1,1),0)

def test_g0_fixture_keeps_identity_separation_explicit():
    assert FIXTURE["Po"] != FIXTURE["Or"]
    assert FIXTURE["Go"] != FIXTURE["Gn"]
    assert "Pog_soft" not in FIXTURE
