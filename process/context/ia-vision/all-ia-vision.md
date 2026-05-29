# IA Vision Context

This file is the canonical IA Vision context entrypoint for DigitalCrown.

Use it after `process/context/all-context.md` when the task needs neural networks, CephLD-CCA inference, or panoramic landmark calibration.

---

## Scope

This group covers:

- Panoramic X-Ray YOLOv11 ONNX object detection and threshold calibrations.
- Cephalometric Profiling U-Net CephLD-CCA PyTorch landmark identification rules.
- Angle calculations (Steiner, Tweed, Normes COM) in the backend.
- Taxonomic classifications of anomalies (Conservatrice, Endo, Paro, etc.) and region ranges.

It does not cover:

- Standard user authentication (that belongs in `auth/` context).
- SQLite client setup (that belongs in `database/` context).

## Read When

Read this entrypoint when:

- adjusting ONNX / PyTorch models runtime execution or confidence thresholds
- correcting cephalometric coordinates calculation formulas
- aligning FDI regions with dental bridges or pathology detections
- modifying AI-generated diagnostic outputs

## Quick Routing

- use `backend/ai_models/` for PyTorch/ONNX source models and wrappers
- use `backend/routers/ia.py` for inference endpoint routers
- use `frontend/src/features/panoramic/` for interactive canvas layers

## Source Paths

- `process/context/ia-vision/all-ia-vision.md`

## Update Triggers

Update this group when:

- Neural network architectures or weights are updated
- Coordinate nomenclature between frontend and backend is updated
- Cephalometric calculation formulas are revised
