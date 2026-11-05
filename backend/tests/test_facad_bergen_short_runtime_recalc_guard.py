"""Bergen Short B4 guarded historic candidate. No clinical parity authority."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from audit import facad_bergen_short_runtime_recalc as c

FIXTURE = Path(__file__).parent / "fixtures/cephalo/bergen_short_f_reconstructed_synthetic.xml"

def points():
    return c.load_markers(FIXTURE)

def test_synthetic_provenance():
    assert 'clinical_authority="false"' in FIXTURE.read_text()
    assert "reconstructed_from=" in FIXTURE.read_text()
    assert len(points()) == 14

def test_12_of_12_historical_ui_values_on_reconstructed_synthetic_case():
    results = c.calculate_bergen_short(points(), 0.2)
    assert set(results) == set(c.FACAD_DISPLAY)
    assert all(value is not None and round(value, 1) == pytest.approx(c.FACAD_DISPLAY[name])
               for name, value in results.items())

@pytest.mark.parametrize("which", ["ray1","ray2"])
def test_angle3_zero_rays_return_none(which):
    p={"N":(0,0),"A":(0,0),"S":(1,0)}
    if which=="ray2":
        p["A"],p["S"]=(1,0),(0,0)
    assert c.angle3(p,"N","A","S") is None

@pytest.mark.parametrize("which", ["first","second"])
def test_angle4_zero_lines_return_none(which):
    p={"A":(0,0),"B":(1,0),"C":(0,0),"D":(0,1)}
    if which=="first": p["B"]=p["A"]
    else: p["D"]=p["C"]
    assert c.angle4(p,"A","B","C","D") is None

def test_point_line_zero_length_return_none():
    assert c.point_line_signed({"A":(0,0),"B":(0,0),"P":(1,2)},"A","B","P",0.2) is None

@pytest.mark.parametrize("bad",[None, math.nan,math.inf,-math.inf,True,0,-1,10**1000])
def test_bad_calibration_refused(bad):
    assert c.point_line_signed(points(),"B","N","Pog",bad) is None

@pytest.mark.parametrize("bad",[(math.nan,3),(math.inf,0),(True,3),(0,10**1000)])
def test_bad_coordinate_refused(bad):
    p=points()
    p["A"]=bad
    assert c.angle3(p,"N","A","S") is None

def test_missing_landmark_refused():
    p=points();del p["N"]
    assert c.angle3(p,"N","A","S") is None
    assert c.point_line_signed(p,"B","N","Pog",0.2) is None

def test_translation_rotation_and_positive_scale_invariant_angle():
    p=points()
    base=c.angle3(p,"N","A","S")
    for fn in [lambda x,y:(x+13,y-79),lambda x,y:(-y,x),lambda x,y:(3*x,3*y)]:
        transformed={k:fn(*v) for k,v in p.items()}
        assert c.angle3(transformed,"N","A","S")==pytest.approx(base)

def test_mirror_reverses_signed_values():
    p=points()
    mirrored={k:(-v[0],v[1]) for k,v in p.items()}
    assert c.angle3(mirrored,"N","A","S")==pytest.approx(-c.angle3(p,"N","A","S"))
    assert c.point_line_signed(mirrored,"B","N","Pog",0.2)==pytest.approx(-c.point_line_signed(p,"B","N","Pog",0.2))

def test_calibration_scale_changes_only_distance():
    assert c.point_line_signed(points(),"B","N","Pog",1.0)==pytest.approx(5*c.point_line_signed(points(),"B","N","Pog",0.2))

def test_cli_synthetic_reconstructed_parity():
    proc=subprocess.run([sys.executable,str(Path(c.__file__)),str(FIXTURE),"--mm-per-pixel","0.2"],capture_output=True,text=True)
    assert proc.returncode==0,proc.stdout+proc.stderr
    result=json.loads(proc.stdout)
    assert result["status"]=="SYNTHETIC_RECONSTRUCTION_PARITY"
    assert len(result["rows"])==12 and all(row["matches_display"] for row in result["rows"])

def test_cli_degenerate_fixture_holds_without_false_success(tmp_path):
    file=tmp_path/"degenerate.xml"
    file.write_text(FIXTURE.read_text().replace("601 102","533 598"))
    proc=subprocess.run([sys.executable,str(Path(c.__file__)),str(file),"--mm-per-pixel","0.2"],capture_output=True,text=True)
    assert proc.returncode!=0
    result=json.loads(proc.stdout)
    assert result["status"]=="HOLD" and result["blocking_factors"]
