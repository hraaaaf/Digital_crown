# P8 — Hardware & Peripheral Compatibility Matrix

**Status:** CLOSED ✅ — **21 EP**

This closeout certifies the **current compatibility boundary** of Digital Crown. It does not claim that a dental device is natively supported merely because its manufacturer supports Windows or macOS.

No direct dental device is certified as `SUPPORTED` in this baseline. That is deliberate: the current product is file-first for clinical imaging, and unsupported direct acquisition stays explicit instead of being decorated with optimistic adjectives.

Vocabulary: `SUPPORTED`, `LIMITED`, `FILE-IMPORT`, `UNSUPPORTED`.

`SUPPORTED` requires both a direct Digital Crown integration **and** a real-device test on every claimed OS. Manufacturer compatibility alone is not Digital Crown compatibility. The machine-readable source of truth is `backend/hardware_compatibility.json`.

## Certified boundary

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

## Repository evidence

### RVG = `FILE-IMPORT`

`RvgUploadModal` exposes a file picker accepting JPEG/PNG/WebP/PDF. `rvgService` sends multipart data to `/documents/patients/{patient_id}/rvg`. The backend validates declared MIME, extension and the 10 MB cap, then archives the bytes.

There is no sensor acquisition API, driver handshake or vendor SDK in this path.

### Panoramic + cephalo = `FILE-IMPORT`

`PanoramicStudio` and `Step1Cephalo` use browser file inputs. `backend/routers/ia.py` receives both modalities as `UploadFile`, writes them locally, then the scientific services read file paths with OpenCV.

Pano/cephalo do not establish DICOM ingestion, TWAIN/WIA/Image Capture, USB/serial acquisition or a vendor sensor SDK.

### QR camera = `LIMITED`

`OnboardingScanner` uses `html5-qrcode`, requires a secure browser context outside localhost and has a manual token fallback. That proves a browser-mediated QR path, **not** native clinical camera support on Windows/macOS.

### Direct hardware stacks = `UNSUPPORTED`

The audited Python requirements do not declare `pydicom`, `pyserial`, `pyusb` or TWAIN stacks. The frontend has `html5-qrcode` but no direct USB/serial browser API is currently used.

## Closure doctrine

P8 is closed because every mandatory hardware/peripheral surface has an explicit, machine-readable Windows/macOS classification and the repository contract fails closed on unsupported promotion.

Closure **does not** freeze the matrix forever. Any future promotion to `SUPPORTED` requires:

1. manufacturer + exact model + firmware/driver;
2. target OS + architecture;
3. official vendor compatibility evidence;
4. Digital Crown adapter/acquisition path;
5. clean install/connect/acquire/reconnect test;
6. correct patient attribution + tenant isolation;
7. denial, unplug/replug, corrupt payload and offline behavior;
8. real-device evidence on every claimed OS.

Until those conditions are present, an unknown direct device defaults to `UNSUPPORTED`.

## Proof contract

The P8 certification workflow validates:

- the ten mandatory surfaces, including the clinical intra-oral camera;
- unique surface identifiers;
- repository evidence for every row;
- format contracts for every `FILE-IMPORT` claim;
- explicit limitations for every `LIMITED` claim;
- real-device evidence before any `SUPPORTED` claim;
- absence of direct DICOM/serial/USB/TWAIN dependencies unless the matrix is deliberately updated;
- RVG, panoramic, cephalo and QR code paths against the current implementation.

Historical regression evidence already exists on the certified P6 candidate: `P8 Hardware` run `32999393352` — SUCCESS. Final P8 closure is effective only when this closeout candidate itself passes `Portability P8 Hardware Compatibility Contract` on the exact HEAD and is merged into the portability integration branch.

No Vercel.
