"""G5 offline research: MedSAM masks on SHA-locked public Aariz radiograph.

No Digital Crown imports, DB access, clinical decisions, or patient records.
Box prompts are UNVERIFIED candidate locations and must be reviewed manually.
"""
from __future__ import annotations

import argparse
from hashlib import md5, sha256
from io import BytesIO
import json
from pathlib import Path

IMAGE_SHA = "7f0746c91faeebbd5a80180b13e0dfa5baa0fe1e0d9403f59f85cf1c03f7eb50"
CHECKPOINT_MD5 = "3bb6db55bd0c9ca30b61248bca72f8d6"
EXPECTED_SIZE = (1935, 2400)
IDS = ("cranial_base", "maxilla", "mandible", "upper_incisor", "lower_incisor", "soft_tissue_profile")
COLORS = ((86,123,181), (48,125,176), (40,174,139), (215,135,65), (226,90,102), (180,100,145))


def load_public_film(*, source_image: Path):
    from PIL import Image
    blob = source_image.read_bytes()
    if sha256(blob).hexdigest() != IMAGE_SHA:
        raise ValueError("G5_PUBLIC_SOURCE_SHA256_MISMATCH")
    image = Image.open(BytesIO(blob)).convert("RGB")
    if image.size != EXPECTED_SIZE:
        raise ValueError("G5_PUBLIC_SOURCE_DIMENSION_MISMATCH")
    return image


def validate_boxes(package: dict):
    import math
    if (not isinstance(package, dict)
        or package.get("schema") != "G5_MEDSAM_RESEARCH_ROIS_V1"
        or package.get("image_sha256") != IMAGE_SHA
        or package.get("approved") is not False
        or package.get("clinical_validation") is not False
        or not isinstance(package.get("boxes"), dict)
        or set(package["boxes"]) != set(IDS)):
        raise ValueError("G5_ROI_CONTRACT_REFUSED")
    for key, box in package["boxes"].items():
        if (not isinstance(box, list) or len(box) != 4
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in box)
            or not (0 <= box[0] < box[2] < EXPECTED_SIZE[0])
            or not (0 <= box[1] < box[3] < EXPECTED_SIZE[1])
            or (box[2] - box[0]) < 12 or (box[3] - box[1]) < 12):
            raise ValueError("G5_BAD_PROMPT_BOX_" + key)


def digest_checkpoint(path: Path) -> str:
    checksum = md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def research_inference(image, boxes: dict, checkpoint: Path, out: Path) -> dict:
    """Original MedSAM ViT-B on CPU, 6 independent box prompts; never a diagnosis."""
    digest = digest_checkpoint(checkpoint)
    if digest != CHECKPOINT_MD5:
        raise ValueError("G5_MED_SAM_CHECKPOINT_NOT_OFFICIAL_ZENODO_MD5")

    import cv2
    import numpy as np
    import torch
    import torch.nn.functional as F
    from skimage import transform
    from segment_anything import sam_model_registry

    model = sam_model_registry["vit_b"](checkpoint=str(checkpoint)).to("cpu").eval()
    w,h = image.size
    img = np.asarray(image)
    square = transform.resize(img, (1024, 1024), order=3,
                              preserve_range=True, anti_aliasing=True).astype(np.uint8)
    square = (square - square.min()) / max(float(square.max() - square.min()), 1e-8)
    tensor = torch.as_tensor(square, dtype=torch.float32).permute(2,0,1).unsqueeze(0)

    qa = {"run":"MEDSAM_RESEARCH_ONLY", "image_sha256":IMAGE_SHA,
          "checkpoint_md5":digest, "approved":False, "clinical_validation":False,
          "coordinate_space":"source_image_pixels",
          "warning":"Automatic segmentation proposal. NO cephalometric or diagnostic validation.",
          "masks":{}}
    composite = np.array(image).copy()
    masks = {}
    with torch.inference_mode():
        embed = model.image_encoder(tensor)
        for index, key in enumerate(IDS):
            coords = np.array(boxes[key], dtype=np.float32)
            box = coords / np.array([w,h,w,h], dtype=np.float32) * 1024
            sparse,dense = model.prompt_encoder(
                points=None,boxes=torch.as_tensor(box).reshape(1,1,4),masks=None)
            lowres,_ = model.mask_decoder(
                image_embeddings=embed,
                image_pe=model.prompt_encoder.get_dense_pe(),
                sparse_prompt_embeddings=sparse,
                dense_prompt_embeddings=dense,
                multimask_output=False)
            full = F.interpolate(torch.sigmoid(lowres),
                size=(h,w), mode="bilinear", align_corners=False)
            mask = (full.squeeze().numpy() > 0.5).astype(np.uint8)
            masks[key] = mask
            outlines,_ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            outlines = sorted(outlines, key=cv2.contourArea, reverse=True)
            for outline in outlines[:7]:
                cv2.drawContours(composite, [outline], -1, COLORS[index], 3)
            pixel_area = int(mask.sum())
            qa["masks"][key] = {
                "pixel_area": pixel_area, "ratio_of_full_image":float(mask.mean()),
                "num_connected_regions":len(outlines),
                "largest_area":float(cv2.contourArea(outlines[0])) if outlines else 0.0,
                "box_source_pixels":boxes[key],
                "basic_quality_hold":pixel_area < 50 or float(mask.mean()) > 0.55,
                "is_clinical_trace":False,
            }
    from PIL import Image
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(composite).save(out / "medsam_six_research_masks_overlay.png")
    np.savez_compressed(out / "medsam_six_research_masks.npz", **masks)
    (out / "medsam_research_qa.json").write_text(
        json.dumps(qa,ensure_ascii=False,indent=2), encoding="utf-8")
    return qa


def main():
    parser=argparse.ArgumentParser(description="Isolated G5 MedSAM public ceph POC; no patient / no clinical approval")
    parser.add_argument("--source-image",type=Path,required=True)
    parser.add_argument("--boxes",type=Path,required=True)
    parser.add_argument("--checkpoint",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--prepare-only",action="store_true")
    parser.add_argument("--acknowledge-research-only",action="store_true")
    args=parser.parse_args()
    image=load_public_film(source_image=args.source_image)
    package=json.loads(args.boxes.read_text(encoding="utf-8"))
    validate_boxes(package)
    if args.prepare_only:
        print("G5_ROI_PREPARED_NO_MODEL_INFERENCE", flush=True)
        return
    if not args.acknowledge_research_only or args.checkpoint is None:
        parser.error("Checkpoint and --acknowledge-research-only required for research masks")
    qa=research_inference(image,package["boxes"],args.checkpoint,args.out)
    print(json.dumps({"status":"UNVALIDATED_RESEARCH_SEGMENTATION","qa":qa}))


if __name__=="__main__":
    main()
