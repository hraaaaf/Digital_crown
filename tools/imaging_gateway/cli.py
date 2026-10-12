"""Explicit opt-in polling CLI. Not a Windows service; no patient upload."""
import argparse
import os
from pathlib import Path
import time

from .gateway import Config, HotFolder


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--watch-dir", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--cabinet", required=True)
    parser.add_argument("--workstation", required=True)
    parser.add_argument("--category", choices=["PHOTO", "RADIOGRAPH"], default="PHOTO")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    key = bytes.fromhex(os.environ["DC_IMAGING_SPOOL_KEY_HEX"])
    gateway = HotFolder(Config(args.cabinet, args.workstation,
                               args.watch_dir, args.state_dir, key, args.category))
    while True:
        print(gateway.scan_once(), flush=True)  # aggregate counts only; no PHI
        if args.once:
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
