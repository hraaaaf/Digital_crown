#!/usr/bin/env python3
"""LOT05/J10O — public academic OPG micro-sample preprocessing benchmark.

First party Mendeley Data V3 record 73n3kz2k4k, university of Kairouan,
CC BY 4.0 publisher label. It has tooth segmentation / EIGHT TOOTH TYPES,
NOT individual 32-class FDI labels. The probe attempts ONE public JPEG,
bounded in size, validates image geometry, never saves it or publishes it.

This is a RESEARCH-only smoke; no FDI accuracy, cloud/commercial legal
clearance or clinical AI model is claimed. No credentials, no GitHub secrets.
"""
from __future__ import annotations
import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DATASET_ID = "73n3kz2k4k"
VERSION = 3
DATASET_API = f"https://api.data.mendeley.com/datasets/{DATASET_ID}?version={VERSION}"
FILES_API = f"https://api.data.mendeley.com/datasets/publics/{DATASET_ID}/files?version={VERSION}&%24limit=100"
FALLBACK_FILES_API = f"https://api.data.mendeley.com/datasets/{DATASET_ID}/files?version={VERSION}"
SCHEMA = "digital-crown-j10o-tunisia-public-opg-sample-v1"
MAX_JPEG_BYTES = 2_000_000
MAX_RESOLUTION_PIXELS = 10_000_000
KNOWN_PUBLIC_DOMAINS = ("data.mendeley.com","api.data.mendeley.com")
VALID_STORAGE_SUFFIX = ".amazonaws.com"


class PublicSampleError(RuntimeError):
    pass


def _public_domain(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and parsed.username is None and parsed.password is None and (
        host in KNOWN_PUBLIC_DOMAINS
        or (host.endswith(VALID_STORAGE_SUFFIX) and host.startswith(("prod-","md-","public-")))
    )


def _read(url: str, max_bytes: int, accept: str) -> bytes:
    if not _public_domain(url):
        raise PublicSampleError("unapproved_public_source_or_redirect")
    request = Request(url, headers={
        "User-Agent": "DigitalCrown-Research-Only-OPG-Sample/1.0",
        "Accept":accept,
    })
    try:
        with urlopen(request, timeout=18) as response:
            if not _public_domain(response.geturl()):
                raise PublicSampleError("untrusted_public_storage_redirect")
            if response.status != 200:
                raise PublicSampleError("public_source_http_not_200")
            body=response.read(max_bytes+1)
    except (HTTPError, URLError) as e:
        raise PublicSampleError("public_academic_endpoint_unavailable:"+type(e).__name__) from e
    if len(body)>max_bytes or not body:
        raise PublicSampleError("public_sample_exceeds_size_limit_or_empty")
    return body


def _api_json(url: str) -> object:
    return json.loads(_read(url,500_000,"application/json"))


def _dataset_check(doc: object) -> dict:
    if not isinstance(doc, dict):
        raise PublicSampleError("dataset_metadata_not_object")
    version=doc.get("version")
    if version!=VERSION:
        raise PublicSampleError("academic_dataset_version_mismatch")
    licence=doc.get("data_licence") or doc.get("data_license") or {}
    if not isinstance(licence,dict) or licence.get("short_name")!="CC BY 4.0":
        raise PublicSampleError("dataset_CC_BY_4_license_not_first_party_verified")
    title=str(doc.get("name") or "").lower()
    if "panoramic" not in title or "dental" not in title:
        raise PublicSampleError("wrong_academic_dataset")
    return {
        "dataset_version": version,
        "declared_academic_dataset_license":"CC BY 4.0",
    }


def _files(doc: object) -> list[dict]:
    if isinstance(doc,list):
        files=doc
    elif isinstance(doc,dict):
        files=doc.get("files") or doc.get("results") or []
    else:
        files=[]
    if not isinstance(files,list):
        raise PublicSampleError("no_dataset_file_list")
    return [x for x in files if isinstance(x,dict)]


def _candidate(files: list[dict]) -> dict:
    candidates=[]
    for f in files:
        filename=f.get("filename") or ""
        size=f.get("size")
        content_details=f.get("content_details") or {}
        if type(filename) is not str or not re.fullmatch(r"[0-9]{1,4}\.jpe?g",filename,re.I):
            continue
        if not isinstance(size,int):
            size=content_details.get("size")
        if type(size) is not int or size<10_000 or size>MAX_JPEG_BYTES:
            continue
        url=content_details.get("download_url")
        fid=f.get("id")
        if not url and type(fid) is str and re.fullmatch(r"[a-f0-9-]{36}",fid):
            # A first-party public dataset read: not a tokenized, synthetic URL.
            url=f"https://api.data.mendeley.com/datasets/{DATASET_ID}/files/{fid}/file_downloaded?version={VERSION}"
        if isinstance(url,str) and _public_domain(url):
            candidates.append((filename,size,url))
    if not candidates:
        raise PublicSampleError("no_public_jpeg_download_url_accessible")
    return {"filename":sorted(candidates)[0][0],"expected_bytes":sorted(candidates)[0][1],
            "source_url":sorted(candidates)[0][2]}


def _decode_image(data: bytes) -> dict:
    from PIL import Image, ImageOps, ImageStat
    if not data.startswith(b"\xff\xd8\xff"):
        raise PublicSampleError("sample_is_not_real_jpeg")
    image=Image.open(BytesIO(data))
    if image.format!="JPEG":
        raise PublicSampleError("unexpected_opg_image_encoding")
    width,height=image.size
    if not (width>=800 and height>=320 and width>height and width*height<=MAX_RESOLUTION_PIXELS):
        raise PublicSampleError("public_panoramic_resolution_invalid")
    # Prevent decompression bombs and non-medical formats; no EXIF saved.
    grey=ImageOps.grayscale(image)
    stat=ImageStat.Stat(grey)
    if float(stat.stddev[0]) < 10 or not (20 < float(stat.mean[0]) < 235):
        raise PublicSampleError("unexpected_grayscale_variance")
    rgb=grey.resize((640,320)).convert("RGB")
    if rgb.size!=(640,320):
        raise PublicSampleError("RGB_preprocessing_failed")
    # Intentionally never output, archive, display, save or hash real image.
    return {
        "published_image_width":width,
        "published_image_height":height,
        "rgb_resized_width":rgb.width,
        "rgb_resized_height":rgb.height,
        "channels_after_preprocessing":len(rgb.getbands()),
        "decode_and_grayscale_preprocessing_pass":True,
    }


def run() -> dict:
    source=_dataset_check(_api_json(DATASET_API))
    listed=None
    for url in (FILES_API,FALLBACK_FILES_API):
        try:
            listed=_files(_api_json(url))
            if listed:
                break
        except PublicSampleError:
            continue
    if not listed:
        raise PublicSampleError("first_party_file_listing_unavailable")
    sample=_candidate(listed)
    raw=_read(sample["source_url"],MAX_JPEG_BYTES,"image/jpeg")
    image=_decode_image(raw)
    return {
        "schema":SCHEMA,
        "status":"PUBLIC_ACADEMIC_OPG_ONE_IMAGE_PREPROCESS_PASS",
        "dataset_id":DATASET_ID,
        "source_record":"doi:10.17632/73n3kz2k4k.3",
        **source,
        **image,
        "public_jpeg_samples_loaded_in_memory":1,
        "total_jpeg_samples_claimed_tested":1,
        "fdi_32_ground_truth_available_for_this_test":False,
        "dental_fdi_accuracy_validated":False,
        "patient_identifiers_exported":False,
        "images_or_weights_uploaded_as_ci_artifact":False,
        "commercial_training_rights_independently_verified":False,
        "clinical_release_approved":False,
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-json",type=Path,required=True)
    args=ap.parse_args()
    args.output_json.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=run()
    except Exception as e:
        result={"schema":SCHEMA,"status":"PUBLIC_ACADEMIC_OPG_TEST_FAIL_CLOSED",
                "reason":type(e).__name__+": "+str(e)[:200],
                "clinical_release_approved":False,
                "commercial_training_rights_independently_verified":False}
        args.output_json.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(result,sort_keys=True))
        return 1
    args.output_json.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
