#!/usr/bin/env python3
"""Byte-exact cosmetic-only diff proof for Wave10. No product behavior changes."""
import json, re, subprocess, pathlib, sys
BASE="505378b0f34122c448d8a6e483e15dd964c70850"
ROOT=pathlib.Path(__file__).resolve().parents[2]
TRANSFORMS={
  "frontend/src/features/admin/SetupWizard/steps/Step5Design.tsx": {
    "text-slate-900": "text-text-main",
    "text-slate-800": "text-text-main",
    "text-slate-500": "text-text-muted",
    "text-slate-400": "text-text-muted",
    "border-slate-200": "border-border-main",
    "border-slate-100": "border-border-main",
    "hover:border-slate-400": "hover:border-border-hover",
    "group-hover:text-slate-800": "group-hover:text-text-main",
    "hover:text-slate-800": "hover:text-text-main",
    "bg-slate-50": "bg-background",
    "hover:bg-slate-50": "hover:bg-background",
    "bg-slate-200": "bg-border-main",
    "bg-white": "bg-card",
    "text-white": "text-on-primary"
  }
}
SKIP={
  "frontend/src/features/admin/SetupWizard/steps/Step5Design.tsx": [
    "w-[32px]",
    "w-24 h-12 flex items-center justify-center bg-white"
  ]
}

def replace_text(text,path):
    lines=[]
    for line in text.split("\n"):
        if any(x in line for x in SKIP.get(path, [])):
            lines.append(line); continue
        out=line
        for old,new in sorted(TRANSFORMS[path].items(), key=lambda x:-len(x[0])):
            out=re.sub(r"(?<![\w/-])"+re.escape(old)+r"(?![\w/-])",lambda _:new,out)
        if path.endswith("PWAInstallPrompt.tsx") and "bg-amber-500" in line:
            out=out.replace("text-text-main","text-on-primary")
        if path.endswith("Step5Design.tsx"):
            out=out.replace('isSelected ? "text-primary" :','isSelected ? "text-text-main" :')
            out=out.replace("bg-card text-primary shadow-sm","bg-card text-text-main shadow-sm")
            out=out.replace('className="ml-auto text-primary"','className="ml-auto text-text-main"')
            out=out.replace('className="absolute top-3 right-3 text-primary"','className="absolute top-3 right-3 text-text-main"')
            out=out.replace("font-medium text-primary","font-medium text-text-main")
        lines.append(out)
    return "\n".join(lines)

def main():
    total=0
    for path in TRANSFORMS:
        before=subprocess.check_output(["git","show",BASE+":"+path],cwd=ROOT).decode("utf-8")
        after=(ROOT/path).read_text(encoding="utf-8")
        expected=replace_text(before,path)
        if after != expected or before==after:
            print("THEME_WAVE10_NON_COSMETIC_DIFF_REFUSED",path)
            return 1
        total+=sum(1 for old,new in TRANSFORMS[path].items() if old in before)
        print("THEME_WAVE10_EXACT_FILE_PASS",path)
    css=(ROOT/"frontend/src/index.css").read_text(encoding="utf-8")
    for theme in ["emerald","rose","ocean","graphite","prestige","dark","high-contrast"]:
        if "[data-theme='"+theme+"']" not in css:
            raise SystemExit("THEME_MISSING_THEME "+theme)
    for role in ["--color-card:","--color-background:","--color-text-main:","--color-text-muted:","--color-border-main:","--color-on-primary:","--color-danger:","--color-success:","--color-info:"]:
        if role not in css:raise SystemExit("THEME_MISSING_ROLE "+role)
    if total < 5:return 1
    print("THEME_WAVE10_COSMETIC_ONLY_PASS",len(TRANSFORMS),"files",total,"mapped source patterns")
    return 0
if __name__=="__main__":sys.exit(main())
