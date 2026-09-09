from __future__ import annotations

import argparse
import re
from pathlib import Path

VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def read_version(path: Path) -> tuple[str, tuple[int, int, int, int]]:
    version = path.read_text(encoding="utf-8").strip()
    match = VERSION_RE.fullmatch(version)
    if not match:
        raise SystemExit(f"Invalid VERSION: {version!r}; expected MAJOR.MINOR.PATCH")
    major, minor, patch = map(int, match.groups())
    return version, (major, minor, patch, 0)


def render(version: str, nums: tuple[int, int, int, int]) -> str:
    numeric = ", ".join(map(str, nums))
    return f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({numeric}),
    prodvers=({numeric}),
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'SANINOVA'),
         StringStruct(u'FileDescription', u'Digital Crown'),
         StringStruct(u'FileVersion', u'{version}'),
         StringStruct(u'InternalName', u'DigitalCrown'),
         StringStruct(u'OriginalFilename', u'DigitalCrown.exe'),
         StringStruct(u'ProductName', u'Digital Crown'),
         StringStruct(u'ProductVersion', u'{version}')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version-file", type=Path, default=Path("VERSION"))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    version, nums = read_version(args.version_file)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(version, nums), encoding="utf-8")
    print(f"WINDOWS_VERSION_INFO=SUCCESS version={version} output={args.output}")


if __name__ == "__main__":
    main()
