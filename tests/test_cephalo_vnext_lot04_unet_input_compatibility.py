import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"run_cephalo_vnext_lot04_unet_baseline_benchmark.py"
spec=importlib.util.spec_from_file_location("lot04_unet",SCRIPT)
mod=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

def test_grayscale_is_replicated_without_intensity_change():
    x=np.array([[0,17],[128,255]],dtype=np.uint8)
    y=mod.ensure_rgb(x)
    assert y.shape==(2,2,3)
    assert np.array_equal(y[:,:,0],x)
    assert np.array_equal(y[:,:,1],x)
    assert np.array_equal(y[:,:,2],x)

def test_rgb_is_unchanged():
    x=np.arange(18,dtype=np.uint8).reshape(2,3,3)
    y=mod.ensure_rgb(x)
    assert y is x
