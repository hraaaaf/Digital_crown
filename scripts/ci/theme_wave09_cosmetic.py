#!/usr/bin/env python3
"""Byte-exact cosmetic-only diff proof for Wave09. No product behavior changes."""
import json, re, subprocess, pathlib, sys
BASE="505378b0f34122c448d8a6e483e15dd964c70850"
ROOT=pathlib.Path(__file__).resolve().parents[2]
TRANSFORMS={
  "frontend/src/features/admin/SetupWizard/steps/Step1Identity.tsx": {
    "text-slate-500": "text-text-muted",
    "text-slate-400": "text-text-muted",
    "text-slate-600": "text-text-main",
    "border-blue-100": "border-border-main",
    "bg-blue-50/50": "bg-card/50",
    "bg-white/70": "bg-card/70",
    "bg-white": "bg-card",
    "text-blue-700": "text-primary",
    "text-blue-900/70": "text-text-muted",
    "border-slate-100": "border-border-main",
    "border-emerald-500": "border-primary",
    "bg-emerald-100": "bg-success-surface",
    "text-emerald-600": "text-success",
    "border-red-300": "border-danger-border",
    "bg-slate-100": "bg-input-field"
  },
  "frontend/src/features/admin/SetupWizard/steps/Step2Specialties.tsx": {
    "text-slate-900": "text-text-main",
    "text-slate-500": "text-text-muted",
    "text-slate-400": "text-text-muted",
    "text-white": "text-on-primary",
    "border-slate-200": "border-border-main",
    "bg-white": "bg-card",
    "border-white/20": "border-border-main",
    "hover:bg-slate-100": "hover:bg-input-field",
    "bg-slate-100": "bg-input-field",
    "text-red-500": "text-danger"
  },
  "frontend/src/features/admin/SetupWizard/steps/Step7Confirmation.tsx": {
    "text-slate-500": "text-text-muted",
    "text-slate-400": "text-text-muted",
    "text-slate-600": "text-text-main",
    "bg-blue-50/60": "bg-card/60",
    "border-blue-100": "border-border-main",
    "text-blue-700": "text-primary",
    "bg-white": "bg-card",
    "bg-emerald-50": "bg-card",
    "border-emerald-100": "border-border-main",
    "text-emerald-600": "text-primary",
    "bg-red-50": "bg-danger-surface",
    "text-red-600": "text-danger",
    "border-red-100": "border-danger-border"
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
            print("THEME_WAVE09_NON_COSMETIC_DIFF_REFUSED",path)
            return 1
        total+=sum(1 for old,new in TRANSFORMS[path].items() if old in before)
        print("THEME_WAVE09_EXACT_FILE_PASS",path)
    css=(ROOT/"frontend/src/index.css").read_text(encoding="utf-8")
    for theme in ["emerald","rose","ocean","graphite","prestige","dark","high-contrast"]:
        if "[data-theme='"+theme+"']" not in css:
            raise SystemExit("THEME_MISSING_THEME "+theme)
    for role in ["--color-card:","--color-background:","--color-text-main:","--color-text-muted:","--color-border-main:","--color-on-primary:","--color-danger:","--color-success:","--color-info:"]:
        if role not in css:raise SystemExit("THEME_MISSING_ROLE "+role)
    if total < 5:return 1
    print("THEME_WAVE09_COSMETIC_ONLY_PASS",len(TRANSFORMS),"files",total,"mapped source patterns")
    return 0
if __name__=="__main__":sys.exit(main())
