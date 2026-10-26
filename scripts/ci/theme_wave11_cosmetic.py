#!/usr/bin/env python3
"""Byte-exact cosmetic-only diff proof for Wave11. No product behavior changes."""
import json, re, subprocess, pathlib, sys
BASE="505378b0f34122c448d8a6e483e15dd964c70850"
ROOT=pathlib.Path(__file__).resolve().parents[2]
TRANSFORMS={
  "frontend/src/pages/ForgotPasswordPage.tsx": {
    "bg-white/80": "bg-card/80",
    "border-white": "border-border-main",
    "text-slate-900": "text-text-main",
    "text-slate-500": "text-text-muted",
    "text-slate-400": "text-text-muted",
    "text-slate-300": "text-text-muted",
    "bg-slate-50/30": "bg-input-field/30",
    "border-slate-100": "border-border-main",
    "bg-red-50": "bg-danger-surface",
    "text-red-600": "text-danger",
    "border-red-100": "border-danger-border",
    "text-white": "text-on-primary",
    "bg-green-50": "bg-success-surface",
    "text-green-500": "text-success",
    "bg-slate-900": "bg-primary",
    "hover:bg-slate-800": "hover:bg-primary/90"
  },
  "frontend/src/components/PWAInstallPrompt.tsx": {
    "bg-slate-800": "bg-card",
    "bg-slate-900": "bg-background",
    "bg-slate-700": "bg-input-field",
    "hover:bg-slate-600": "hover:bg-background",
    "text-white": "text-text-main",
    "text-slate-300": "text-text-muted",
    "text-amber-400": "text-text-main",
    "border-slate-700": "border-border-main",
    "border-slate-600": "border-border-hover",
    "border-slate-400": "border-border-main",
    "bg-blue-500": "bg-info",
    "text-blue-400": "text-text-main",
    "bg-amber-500": "bg-primary",
    "hover:bg-amber-600": "hover:bg-primary/90"
  }
}
SKIP={}

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
        lines.append(out)
    return "\n".join(lines)

def main():
    total=0
    for path in TRANSFORMS:
        before=subprocess.check_output(["git","show",BASE+":"+path],cwd=ROOT).decode("utf-8")
        after=(ROOT/path).read_text(encoding="utf-8")
        expected=replace_text(before,path)
        if after != expected or before==after:
            print("THEME_WAVE11_NON_COSMETIC_DIFF_REFUSED",path)
            return 1
        total+=sum(1 for old,new in TRANSFORMS[path].items() if old in before)
        print("THEME_WAVE11_EXACT_FILE_PASS",path)
    css=(ROOT/"frontend/src/index.css").read_text(encoding="utf-8")
    for theme in ["emerald","rose","ocean","graphite","prestige","dark","high-contrast"]:
        if "[data-theme='"+theme+"']" not in css:
            raise SystemExit("THEME_MISSING_THEME "+theme)
    for role in ["--color-card:","--color-background:","--color-text-main:","--color-text-muted:","--color-border-main:","--color-on-primary:","--color-danger:","--color-success:","--color-info:"]:
        if role not in css:raise SystemExit("THEME_MISSING_ROLE "+role)
    if total < 5:return 1
    print("THEME_WAVE11_COSMETIC_ONLY_PASS",len(TRANSFORMS),"files",total,"mapped source patterns")
    return 0
if __name__=="__main__":sys.exit(main())
