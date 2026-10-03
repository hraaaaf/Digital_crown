import math
from backend.services.cephalo_steiner_geometry import (
    steiner_u1_na_mm_v1, steiner_l1_nb_mm_v1, steiner_pog_nb_mm_v1,
    steiner_l1_gogn_deg_v1, steiner_occlusal_sn_deg_v1, steiner_snd_deg_v1,
    steiner_l1_dline_mm_v1, steiner_l1_dline_deg_v1,
)

def test_linear_distances_require_explicit_surface_and_calibration():
    assert steiner_u1_na_mm_v1((3,4),(0,0),(0,10),0.5)==1.5
    assert steiner_l1_nb_mm_v1((4,2),(0,0),(0,10),0.5)==2.0
    assert steiner_pog_nb_mm_v1((6,2),(0,0),(0,10),0.5)==3.0
    assert steiner_u1_na_mm_v1(None,(0,0),(0,10),0.5) is None
    assert steiner_u1_na_mm_v1((3,4),(0,0),(0,10),None) is None

def test_steiner_angular_extensions_are_deterministic():
    assert math.isclose(steiner_l1_gogn_deg_v1((0,0),(0,10),(0,0),(10,0)),90.0)
    assert math.isclose(steiner_occlusal_sn_deg_v1((0,0),(10,0),(0,0),(10,10)),45.0)
    assert math.isclose(steiner_snd_deg_v1((-10,0),(0,0),(0,10)),90.0)

def test_dline_geometry_uses_explicit_d_and_go_gn():
    assert steiner_l1_dline_mm_v1((4,7),(1,2),(1,0),(11,0),0.5)==1.5
    assert math.isclose(steiner_l1_dline_deg_v1((0,0),(10,0),(0,0),(10,0)),90.0)

def test_extensions_fail_closed_on_degenerate_geometry():
    assert steiner_l1_gogn_deg_v1((0,0),(0,1),(1,1),(1,1)) is None
    assert steiner_occlusal_sn_deg_v1((0,0),(0,0),(0,0),(1,0)) is None
    assert steiner_l1_dline_mm_v1((1,1),(0,0),(2,2),(2,2),1.0) is None
