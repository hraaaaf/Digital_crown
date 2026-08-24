# P8 — Hardware & Peripheral Compatibility Matrix

**Status:** ACTIVE — audit baseline only. **0 EP credited.**

Vocabulary: `SUPPORTED`, `LIMITED`, `FILE-IMPORT`, `UNSUPPORTED`.

`SUPPORTED` requires both a direct Digital Crown integration **and** a real-device test on every claimed OS. Manufacturer compatibility alone is not Digital Crown compatibility. The machine-readable source of truth is `backend/hardware_compatibility.json`.

## Verified baseline

| Surface | Windows | macOS | Current Digital Crown path | Direct acquisition |
|---|---|---|---|---|
| RVG / intra-oral radiographs | FILE-IMPORT | FILE-IMPORT | Patient > Radiology > RVG upload; JPEG/PNG/WebP/PDF, max 10 MB | UNSUPPORTED |
| Panoramic / OPG | FILE-IMPORT | FILE-IMPORT | `/api/ia/upload-panoramic` -> file -> OpenCV/ONNX | UNSUPPORTED |
| Cephalometric radiograph | FILE-IMPORT | FILE-IMPORT | `/api/ia/upload-radio` -> file -> CephaloService/OpenCV | UNSUPPORTED |
| DICOM `.dcm` / PACS | UNSUPPORTED | UNSUPPORTED | No DICOM parser/import contract identified | UNSUPPORTED |
| TWAIN / WIA / Image Capture | UNSUPPORTED | UNSUPPORTED | No device-acquisition integration identified | UNSUPPORTED |
| USB / serial / vendor SDK | UNSUPPORTED | UNSUPPORTED | No WebUSB/WebSerial/pyusb/pyserial/vendor adapter identified | UNSUPPORTED |
| Mobile/browser camera for ZKA pairing | LIMITED | LIMITED | `html5-qrcode`; secure-context gate; manual fallback | QR pairing only |
| Clinical intra-oral camera | FILE-IMPORT | FILE-IMPORT | Resulting image can be archived/imported; no camera control | UNSUPPORTED |
| Standard printer | LIMITED | LIMITED | PDF/OS-mediated output | OS-mediated only |
| Optical dental scanner / STL / PLY | UNSUPPORTED | UNSUPPORTED | No scanner SDK or STL/PLY clinical import contract identified | UNSUPPORTED |

## Verified code evidence

### RVG = `FILE-IMPORT`

`RvgUploadModal` exposes a file picker accepting JPEG/PNG/WebP/PDF. `rvgService` sends multipart data to `/documents/patients/{patient_id}/rvg`. The backend validates declared MIME, extension and the 10 MB cap, then archives the bytes.

There is no sensor acquisition API, driver handshake or vendor SDK in this path.

### Panoramic + cephalo = `FILE-IMPORT`

`PanoramicStudio` and `Step1Cephalo` use browser file inputs. `backend/routers/ia.py` receives both modalities as `UploadFile`, writes them locally, then the scientific services read file paths with OpenCV.

Hardening debt: pano/cephalo do not yet share the stricter RVG MIME + extension contract, and none of the audited imaging upload paths prove DICOM ingestion.

### QR camera = `LIMITED`

`OnboardingScanner` uses `html5-qrcode`, requires a secure browser context outside localhost and has a manual token fallback. That proves a browser-mediated QR path, **not** native camera support on Windows/macOS and not clinical imaging acquisition.

### Direct hardware stacks = `UNSUPPORTED`

The audited Python requirements do not declare `pydicom`, `pyserial`, `pyusb` or TWAIN stacks. The frontend has `html5-qrcode` but no direct USB/serial browser API is currently used.

## P8 doctrine

Keep the universal baseline **file-first**. Add direct vendor adapters only when a named commercial need justifies the driver/SDK maintenance burden.

A future device can move to `SUPPORTED` only with:

1. manufacturer + exact model + firmware/driver;
2. target OS + architecture;
3. official vendor compatibility evidence;
4. Digital Crown adapter/acquisition path;
5. clean install/connect/acquire/reconnect test;
6. correct patient attribution + tenant isolation;
7. denial, unplug/replug, corrupt payload and offline behavior;
8. real-device evidence on every claimed OS.

## Open gates

P8 remains **OPEN**. No named dental device has real-device evidence yet. The current baseline is deliberately conservative and portable.
