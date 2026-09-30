[CmdletBinding()]
param(
    [string]$RuntimeRoot = (Join-Path $env:USERPROFILE 'DigitalCrown-Runtime'),
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'Programs\DigitalCrown'),
    [string]$DesktopPath = [Environment]::GetFolderPath('Desktop')
)

$ErrorActionPreference = 'Stop'

if (-not $DesktopPath) {
    throw 'Desktop path is unavailable.'
}

$installedExe = Join-Path $InstallRoot 'DigitalCrown.exe'
$runtimeLauncher = Join-Path $RuntimeRoot 'bin\open_digitalcrown.ps1'
$shortcutPath = Join-Path $DesktopPath 'DigitalCrown.lnk'

if (Test-Path -LiteralPath $installedExe) {
    $targetPath = $installedExe
    $arguments = ''
    $workingDirectory = $InstallRoot
    $iconLocation = $installedExe
}
elseif (Test-Path -LiteralPath $runtimeLauncher) {
    $targetPath = (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')
    $arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $runtimeLauncher + '"'
    $workingDirectory = $RuntimeRoot
    $iconLocation = (Join-Path $env:SystemRoot 'System32\shell32.dll') + ',220'
}
else {
    throw "No supported Digital Crown launcher found. Expected '$installedExe' or '$runtimeLauncher'."
}

New-Item -ItemType Directory -Path $DesktopPath -Force | Out-Null

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.Arguments = $arguments
$shortcut.WorkingDirectory = $workingDirectory
$shortcut.Description = 'Lancer Digital Crown sans terminal'
$shortcut.IconLocation = $iconLocation
$shortcut.Save()

$verify = $shell.CreateShortcut($shortcutPath)
if ($verify.TargetPath -ne $targetPath -or $verify.WorkingDirectory -ne $workingDirectory) {
    throw 'Desktop shortcut verification failed.'
}
if ($arguments -and $verify.Arguments -ne $arguments) {
    throw 'Desktop shortcut arguments verification failed.'
}

Write-Output "DIGITALCROWN_SHORTCUT_OK=$shortcutPath"
Write-Output "TARGET=$($verify.TargetPath)"
Write-Output "WORKDIR=$($verify.WorkingDirectory)"
