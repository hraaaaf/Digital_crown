import json
import subprocess
import sys
from pathlib import Path

def test_facad_cph_parser_extracts_norm_bearing_measurements(tmp_path):
    src = tmp_path / "sample.cph"
    src.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<Facad>
  <version>3,11,0</version>
  <saved>2020-06-08 17:40:36</saved>
  <cephfile>
    <name>Ricketts (2 F)</name>
    <AnalysisType>Lateral</AnalysisType>
    <analysis>
      <name>Facial depth</name>
      <norm>90±3</norm>
      <unit>deg</unit>
      <calc_type>Angle</calc_type>
      <point_ref>N</point_ref>
      <point_ref>Pog</point_ref>
    </analysis>
    <analysis>
      <name>Convexity</name>
      <norm>2±2</norm>
      <unit>mm</unit>
      <calc_type>DistLine</calc_type>
      <changeSign>true</changeSign>
      <point_ref>A</point_ref>
    </analysis>
    <marker><name>N</name></marker>
  </cephfile>
</Facad>
""", encoding="utf-8")
    out = tmp_path / "out.json"
    subprocess.run(
        [sys.executable, "audit/cephalo_lot08_facad_cph_parse.py", str(src), "--out", str(out)],
        check=True,
    )
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 1
    profile = data[0]
    assert profile["profile_name"] == "Ricketts (2 F)"
    assert profile["measurement_candidate_count"] == 2
    assert [m["name"] for m in profile["measurement_candidates"]] == ["Facial depth", "Convexity"]
    assert profile["measurement_candidates"][1]["changeSign"] == "true"
    assert profile["measurement_candidates"][0]["point_refs"] == ["N", "Pog"]
