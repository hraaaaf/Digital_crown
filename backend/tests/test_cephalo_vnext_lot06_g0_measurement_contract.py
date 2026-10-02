import math

from backend.services.cephalo_constructions import (
    craniom_ab_prime_mm_v1,
    craniom_facial_depth_mm_v1,
    nasion_vertical_offset_mm_v1,
)
from backend.services.cephalo_craniom_angular import (
    craniom_interincisal_deg_v1,
    craniom_u1_frankfort_deg_v1,
)
from backend.services.cephalo_mcnamara_geometry import (
    mcnamara_ans_me_mm_v1,
    mcnamara_co_a_mm_v1,
    mcnamara_co_gn_mm_v1,
)
from backend.services.cephalo_steiner_geometry import (
    steiner_anb_deg_v1,
    steiner_l1_nb_deg_v1,
    steiner_sna_deg_v1,
    steiner_snb_deg_v1,
    steiner_sn_mp_deg_v1,
    steiner_u1_na_deg_v1,
)
from backend.services.cephalo_downs_geometry import downs_facial_angle_deg_v1
from backend.services.cephalo_ricketts_geometry import ricketts_facial_depth_deg_v1
from backend.services.cephalo_tweed_merrifield_geometry import (
    tweed_fma_deg_v1,
    tweed_fmia_deg_v1,
    tweed_impa_deg_v1,
)

def close(actual, expected):
    assert actual is not None
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-9)

def test_lot06_g0_angular_contracts():
    n=(0.0,0.0); s=(-1.0,0.0); a=(0.0,1.0); b=(0.0,-1.0)
    close(steiner_sna_deg_v1(s,n,a),90.0)
    close(steiner_snb_deg_v1(s,n,b),90.0)
    close(steiner_anb_deg_v1(s,n,a,b),0.0)
    close(steiner_sn_mp_deg_v1((0,0),(1,0),(0,1),(1,1)),0.0)
    close(steiner_u1_na_deg_v1((0,0),(0,1),(0,0),(1,0)),90.0)
    close(steiner_l1_nb_deg_v1((0,0),(0,1),(0,0),(1,0)),90.0)
    close(tweed_fma_deg_v1((0,0),(1,0),(0,1),(1,1)),0.0)
    close(tweed_impa_deg_v1((0,0),(0,1),(0,0),(1,0)),90.0)
    close(tweed_fmia_deg_v1((0,0),(0,1),(0,0),(1,0)),90.0)
    close(craniom_u1_frankfort_deg_v1((0,0),(0,1),(0,0),(1,0)),90.0)
    close(craniom_interincisal_deg_v1((0,0),(0,1),(0,0),(1,0)),90.0)

def test_lot06_g0_linear_contracts_require_calibration():
    close(mcnamara_co_a_mm_v1((0,0),(3,4),0.5),2.5)
    close(mcnamara_co_gn_mm_v1((0,0),(3,4),0.5),2.5)
    close(mcnamara_ans_me_mm_v1((0,0),(3,4),0.5),2.5)
    close(nasion_vertical_offset_mm_v1((2,3),(0,0),(0,0),(1,0),0.5),1.0)
    close(craniom_facial_depth_mm_v1((2,3),(0,0),(0,0),(1,0),0.5),1.0)
    close(craniom_ab_prime_mm_v1((3,0),(1,0),(0,0),(1,0),0.5),1.0)

def test_lot06_g0_fail_closed_on_missing_or_degenerate_inputs():
    assert steiner_sna_deg_v1(None,(0,0),(1,0)) is None
    assert steiner_sn_mp_deg_v1((0,0),(0,0),(0,1),(1,1)) is None
    assert tweed_fma_deg_v1((0,0),(0,0),(0,1),(1,1)) is None
    assert tweed_impa_deg_v1((0,0),(0,0),(0,1),(1,1)) is None
    assert mcnamara_co_a_mm_v1((0,0),(3,4),None) is None
    assert mcnamara_co_gn_mm_v1(None,(3,4),0.5) is None
    assert mcnamara_ans_me_mm_v1((0,0),(3,4),0.0) is None
    assert nasion_vertical_offset_mm_v1((2,3),(0,0),(0,0),(0,0),0.5) is None
    assert craniom_ab_prime_mm_v1((3,0),(1,0),(0,0),(0,0),0.5) is None
    assert craniom_facial_depth_mm_v1((2,3),(0,0),(0,0),(0,0),0.5) is None


def test_lot06_g0_facial_angle_conventions_are_not_silently_merged():
    po=(0.0,0.0); orbitale=(1.0,0.0); n=(0.0,1.0); pog=(1.0,0.0)
    close(downs_facial_angle_deg_v1(po,orbitale,n,pog),45.0)
    close(ricketts_facial_depth_deg_v1(po,orbitale,n,pog),135.0)
