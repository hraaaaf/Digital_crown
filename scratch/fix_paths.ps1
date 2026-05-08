$files = @(
    "backend/services/generators/accounting_gen.py",
    "backend/services/generators/ordonnance_gen.py",
    "backend/services/generators/libre_gen.py",
    "backend/services/generators/certificat_gen.py"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw
        # Pattern pour accounting_gen (Simple return)
        $content = $content -replace 'return filepath\[filepath\.find\("static"\):\]\.replace\("\\", "/"\)', 'return filepath.replace("\\", "/")'
        
        # Pattern pour les autres (relative_path logic)
        $content = $content -replace 'relative_path = filepath\[filepath\.find\("static"\):\] if "static" in filepath else filepath\s+return relative_path\.replace\("\\", "/"\)', 'return filepath.replace("\\", "/")'
        
        [System.IO.File]::WriteAllText((Get-Item $file).FullName, $content)
        Write-Host "Fixed $file"
    } else {
        Write-Warning "File not found: $file"
    }
}
