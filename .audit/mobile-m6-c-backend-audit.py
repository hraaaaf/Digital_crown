from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
legacy_path = root / 'backend/routers/mobile_legacy.py'
pad_path = root / 'frontend/src/features/mobile/Dashboard/components/SignaturePad.tsx'
modal_path = root / 'frontend/src/features/mobile/Dashboard/components/SignatureModal.tsx'

legacy = legacy_path.read_text(encoding='utf-8')
pad = pad_path.read_text(encoding='utf-8')
modal = modal_path.read_text(encoding='utf-8')

tree = ast.parse(legacy)
function = next(node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == 'sign_mobile_document')
segment = ast.get_source_segment(legacy, function) or ''

report = {
    'signRouteFound': bool(segment),
    'patientsPermissionRequired': 'require_mobile_permission("patients")' in segment,
    'tenantPatientOwnershipCheckVisible': 'doc.patient_id' in segment and 'models.Patient.employer_id == employer_id' in segment,
    'base64Decoded': 'base64.b64decode(sig_data)' in segment,
    'signatureBytesWrittenDirectly': 'f.write(sig_bytes)' in segment,
    'imageContentValidationVisible': any(token in segment for token in ('Image.open', 'PIL.', 'verify()', 'image.verify')),
    'signatureByteLimitVisible': any(token in segment for token in ('len(sig_bytes)', 'MAX_SIGNATURE', 'SIGNATURE_MAX', 'max_signature')),
    'alreadySignedGuardVisible': any(token in segment for token in ('already signed', 'déjà signé', 'deja signe', 'cdata.get("signed")', "cdata.get('signed')")),
    'fixedCanvasBacking300x180': 'width={300}' in pad and 'height={180}' in pad,
    'devicePixelRatioHandled': 'devicePixelRatio' in pad,
    'blankInkGuardVisible': any(token in pad for token in ('hasInk', 'isEmpty', 'hasDrawn', 'hasSignature')),
    'saveDirectlySerializesCanvas': 'onSave(canvas.toDataURL())' in pad,
    'signedDocumentsRemainSelectable': "{d.signed ? 'SIGNÉ' : 'Non signé'}" in modal and 'disabled={d.signed}' not in modal,
    'emptyStateCopyMentionsOnlyDevis': 'Aucun devis trouvé pour ce patient' in modal,
}

out = root / 'mobile-m6-c-backend-audit.json'
out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps(report, indent=2, ensure_ascii=False))

if not report['signRouteFound']:
    raise SystemExit('M6-C audit could not find sign_mobile_document')
