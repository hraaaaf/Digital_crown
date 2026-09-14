"""Lock an exact insurance/NGAP PDF into Digital Crown's immutable local source store.

Examples:
  python scripts/lock_insurance_source.py --kind ngap --file ./177-06.pdf \
      --source-url https://www.sante.gov.ma/.../177-06.pdf

  python scripts/lock_insurance_source.py --kind cnss --file ./610-1-04.pdf \
      --source-url cabinet://validated/CNSS-610-1-04.pdf \
      --confirm-cabinet-validation
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.core.media_paths import get_media_root
from backend.services.insurance_source_store import (
    lock_and_store_insurance_template,
    lock_and_store_ngap_primary,
)
from backend.services.insurance_template_registry import (
    CNOPS_DENTAL_PENDING,
    CNSS_610_1_04,
    FAR_2021_1,
    InsuranceTemplateTrust,
)
from backend.services.ngap_reference import DENTAL_NGAP_PRIMARY_PENDING


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, SHA-256 lock and immutably store an insurance source PDF."
    )
    parser.add_argument("--kind", choices=("ngap", "cnss", "cnops", "far"), required=True)
    parser.add_argument("--file", required=True, help="Local PDF path")
    parser.add_argument("--source-url", required=True, help="Official URL or cabinet provenance URI")
    parser.add_argument(
        "--store-root",
        default=str(get_media_root() / "insurance_sources"),
        help="Immutable local store root",
    )
    parser.add_argument(
        "--confirm-cabinet-validation",
        action="store_true",
        help="Required before a CABINET_VALIDATED_BINARY template can be locked",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    pdf_path = Path(args.file).expanduser().resolve()
    if not pdf_path.is_file():
        raise SystemExit(f"PDF source not found: {pdf_path}")
    pdf_bytes = pdf_path.read_bytes()
    root = Path(args.store_root).expanduser().resolve()

    if args.kind == "ngap":
        locked, stored = lock_and_store_ngap_primary(
            root=root,
            release=DENTAL_NGAP_PRIMARY_PENDING,
            pdf_bytes=pdf_bytes,
            source_url=args.source_url,
        )
        result = {
            "kind": "ngap",
            "version": locked.version,
            "status": locked.status.value,
            "sha256": locked.source_hash,
            "source_url": locked.source_url,
            "publication_reference": locked.publication_reference,
            "stored_pdf": stored.pdf_path,
            "manifest": stored.manifest_path,
        }
    else:
        definitions = {
            "cnss": CNSS_610_1_04,
            "cnops": CNOPS_DENTAL_PENDING,
            "far": FAR_2021_1,
        }
        definition = definitions[args.kind]
        if (
            definition.trust == InsuranceTemplateTrust.CABINET_VALIDATED_BINARY
            and not args.confirm_cabinet_validation
        ):
            raise SystemExit(
                "This template is CABINET_VALIDATED_BINARY: rerun with "
                "--confirm-cabinet-validation only after explicit practitioner validation."
            )
        locked, stored = lock_and_store_insurance_template(
            root=root,
            definition=definition,
            pdf_bytes=pdf_bytes,
            source_url=args.source_url,
        )
        result = {
            "kind": "template",
            "organization": definition.organization.value,
            "version": definition.version,
            "trust": definition.trust.value,
            "sha256": locked.sha256,
            "page_count": locked.page_count,
            "source_url": locked.source_url,
            "stored_pdf": stored.pdf_path,
            "manifest": stored.manifest_path,
        }

    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
