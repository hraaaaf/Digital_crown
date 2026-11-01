#Requires -Version 7.0
# Disposable child's own Windows token performs real native checks.
param(
  [Parameter(Mandatory)][string]$PipeName,
  [Parameter(Mandatory)][string]$ExpectedSid,
  [Parameter(Mandatory)][int]$ParentPid,
  [Parameter(Mandatory)][ValidateSet(0,5)][int]$ExpectedOpen,
  [Parameter(Mandatory)][ValidateSet(0,5)][int]$ExpectedCreateInstance
)
$ErrorActionPreference = 'Stop'
try {
  if (-not $IsWindows -or $PID -eq $ParentPid) {
    throw 'C05B03R_NOT_SEPARATE_WINDOWS_PROCESS'
  }
  $who=[System.Security.Principal.WindowsIdentity]::GetCurrent()
  try {
    if ($who.User.Value -ne $ExpectedSid) {
      throw 'C05B03R_REAL_USER_SID_MISMATCH'
    }
  } finally { $who.Dispose() }
  Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class DC06RClient {
    [DllImport("kernel32.dll", EntryPoint="CreateFileW", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern SafeFileHandle CreateFile(string path, uint desired, uint share,
        IntPtr security, uint disposition, uint flags, IntPtr template);

    [DllImport("kernel32.dll", EntryPoint="CreateNamedPipeW", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern SafeFileHandle CreatePipe(string path, uint mode, uint type, uint maxInstances,
        uint outSize, uint inSize, uint timeout, IntPtr attributes);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool WriteFile(SafeFileHandle file, byte[] buffer, uint count,
        out uint written, IntPtr overlapped);

    public static int ClientOpen(string path) {
        // FILE_READ_DATA | FILE_WRITE_DATA | FILE_READ_ATTRIBUTES |\n        // FILE_WRITE_ATTRIBUTES | SYNCHRONIZE; NEVER FILE_APPEND_DATA
        // since that bit equals FILE_CREATE_PIPE_INSTANCE for named pipes.
        using (var handle = CreateFile(path, 0x00100183u, 0u, IntPtr.Zero,
                                       3u, 0u, IntPtr.Zero)) {
            if (handle.IsInvalid) return Marshal.GetLastWin32Error();
            byte[] one = new byte[] { 82 };
            uint wrote;
            if (!WriteFile(handle, one, 1u, out wrote, IntPtr.Zero) || wrote != 1u)
                return Marshal.GetLastWin32Error();
            return 0;
        }
    }

    public static int InstanceAttempt(string path) {
        // Without FIRST_PIPE_INSTANCE: this is a direct check of DACL rights,
        // NOT the earlier Q first-instance guard.
        using (var handle = CreatePipe(path, 3u, 8u, 4u, 4096u, 4096u,
                                       5000u, IntPtr.Zero)) {
            return handle.IsInvalid ? Marshal.GetLastWin32Error() : 0;
        }
    }
}
'@
  $open=[DC06RClient]::ClientOpen($PipeName)
  if ($open -ne $ExpectedOpen) {
    throw ('C05B03R_CHILD_OPEN_EXPECT_' + $ExpectedOpen + '_GOT_' + $open)
  }
  $created=[DC06RClient]::InstanceAttempt($PipeName)
  if ($created -ne $ExpectedCreateInstance) {
    throw ('C05B03R_CHILD_CREATE_INSTANCE_EXPECT_' + $ExpectedCreateInstance +
        '_GOT_' + $created)
  }
  if ($ExpectedOpen -eq 0) {
    Write-Output 'C05B03R_ALLOWED_USER_READ_WRITE_ALLOWED_INSTANCE_CREATION_DENIED'
  } else {
    Write-Output 'C05B03R_UNAUTHORIZED_SECOND_USER_OPEN_AND_INSTANCE_DENIED'
  }
  exit 0
} catch {
  Write-Error ('C05B03R_CHILD_FAIL: ' + $_.Exception.Message)
  exit 44
}
