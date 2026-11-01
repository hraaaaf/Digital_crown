#Requires -Version 7.0
# LOT06-Q child only, started by Windows with a DIFFERENT local user account.
# No credentials in args. Only expects OS-native CreateFileW ACCESS_DENIED(5).
param(
  [Parameter(Mandatory)][string]$PipeName,
  [Parameter(Mandatory)][string]$ExpectedSid,
  [Parameter(Mandatory)][int]$ParentPid
)
$ErrorActionPreference='Stop'
try {
  if (-not $IsWindows) { throw "C05B03Q_NOT_WINDOWS" }
  if ($PID -eq $ParentPid) { throw "C05B03Q_SAME_PROCESS_NOT_VALID_EVIDENCE" }
  $identity=[System.Security.Principal.WindowsIdentity]::GetCurrent()
  try {
    if ($identity.User.Value -ne $ExpectedSid) {
      throw "C05B03Q_CHILD_NOT_ACTUAL_DIFFERENT_OS_USER"
    }
    if ($identity.IsSystem) { throw "C05B03Q_CHILD_SYSTEM_IDENTITY_FORBIDDEN" }
  } finally { $identity.Dispose() }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class DC06QNativeClient {
    [DllImport("kernel32.dll", EntryPoint="CreateFileW", CharSet=CharSet.Unicode,
        SetLastError=true)]
    public static extern SafeFileHandle CreateFile(
        string filename, uint access, uint share,
        IntPtr security, uint disposition, uint flags, IntPtr template);

    public static int Test(string pipe) {
        using (var handle=CreateFile(pipe, 0xC0000000u, 0, IntPtr.Zero, 3, 0,
                                     IntPtr.Zero)) {
            return handle.IsInvalid ? Marshal.GetLastWin32Error() : 0;
        }
    }
}
'@
  $code=[DC06QNativeClient]::Test($PipeName)
  if ($code -ne 5) { throw ("C05B03Q_UNAUTHORIZED_PROCESS_NOT_DENIED_WIN32_" + $code) }
  Write-Output "C05B03Q_CHILD_REAL_SECOND_PROCESS_REAL_SECOND_USER_DENIED_5"
  exit 0
}
catch {
  Write-Error ("C05B03Q_CHILD_CHECK_FAILED: " + $_.Exception.Message)
  exit 31
}
