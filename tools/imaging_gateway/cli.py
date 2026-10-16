"""Explicit opt-in polling CLI. Not a Windows service; no patient upload."""
import argparse
import os
from pathlib import Path
import time

from .gateway import Config, HotFolder
from .operations import project_operations, render_operations_text, render_operations_json, render_operations_html


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--cabinet", required=True)
    parser.add_argument("--workstation", required=True)
    parser.add_argument("--category", choices=["PHOTO", "RADIOGRAPH"], default="PHOTO")
    parser.add_argument("--require-ready-manifest", action="store_true",
                        help="Stage only files with a matching .ready SHA-256/size manifest")
    parser.add_argument("--max-spool-mib", type=int, default=2048)
    parser.add_argument("--max-queue-items", type=int, default=1000)
    parser.add_argument("--min-free-mib", type=int, default=64)
    display = parser.add_mutually_exclusive_group()
    display.add_argument("--operations", action="store_true",
                         help="Read-only local operator checklist; no patient association")
    display.add_argument("--operations-html", action="store_true",
                         help="Print a static mobile-friendly offline read-only HTML preview")
    display.add_argument("--operations-json", action="store_true",
                         help="No-PHI JSON contract for future authorized UI")
    display.add_argument("--health", action="store_true",
                        help="Show aggregate local storage health only; do not scan")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    key = bytes.fromhex(os.environ["DC_IMAGING_SPOOL_KEY_HEX"])
    gateway = HotFolder(Config(args.cabinet, args.workstation,
                               args.watch_dir, args.state_dir, key, args.category,
                               require_ready_manifest=args.require_ready_manifest,
                               max_spool_bytes=args.max_spool_mib * 1024 ** 2,
                               max_queue_items=args.max_queue_items,
                               min_free_bytes=args.min_free_mib * 1024 ** 2))
    if args.health:
        print(gateway.storage_health(), flush=True)  # No paths, patient data or digests
        return
    if args.operations or args.operations_json or args.operations_html:
        view = project_operations(gateway.storage_health())
        rendered = (render_operations_html(view) if args.operations_html else
                    render_operations_json(view) if args.operations_json else
                    render_operations_text(view))
        print(rendered, flush=True)
        return
    while True:
        print(gateway.scan_once(), flush=True)  # aggregate counts only; no PHI
        if args.once:
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
