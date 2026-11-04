#Requires -Version 7.0
# Disposable child's own Windows token performs real native checks.
param(
  [Parameter(Mandatory)][string]$PipeName,
  [Parameter(Mandatory)][string]$ExpectedSid,
  [Parameter(Mandatory)][int]$ParentPid,
  [Parameter(Mandatory)][ValidateSet(0,5)][int]$ExpectedOpen,
  [Parameter(Mandatory)][ValidateSet(0,5)][int]$ExpectedCreateInstance,
  [switch]$ProbeQueueReadOnly,
  [ValidateSet('None','Valid','Tampered','WrongKey')][string]$B03Status='None',
  [switch]$ProbeB05Package,
  [ValidateSet('None','Valid','Tampered','WrongKey','Unauthorized')][string]$B06InventoryStatus='None',
  [ValidateSet('None','Valid','Tampered','WrongKey','Unauthorized')][string]$B06MediaStatus='None',
  [string]$B05KeyFile='',
  [string]$B05ServiceDll='',
  [string]$B05BinDirectory=''
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

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern bool ReadFile(SafeFileHandle file,
        [Out] byte[] buffer, uint count, out uint read, IntPtr overlapped);

    public static int ReadOnlyStatus(string path) {
        using (var handle = CreateFile(path, 0x00100183u, 0u, IntPtr.Zero,
                                       3u, 0u, IntPtr.Zero)) {
            if (handle.IsInvalid) return -1000 - Marshal.GetLastWin32Error();
            uint wrote;
            if (!WriteFile(handle, new byte[]{(byte)'Q'}, 1u, out wrote, IntPtr.Zero)
                    || wrote != 1u) return -2000;
            byte[] answer = new byte[1];
            uint read;
            if (!ReadFile(handle, answer, 1u, out read, IntPtr.Zero)
                    || read != 1u) return -3000;
            return (int)answer[0];
        }
    }

    public static string B03Status(string path) {
        using (var handle = CreateFile(path, 0x00100183u, 0u, IntPtr.Zero,
                                       3u, 0u, IntPtr.Zero)) {
            if (handle.IsInvalid) return "OPEN_ERROR";
            uint written;
            if (!WriteFile(handle, new byte[] {(byte)'S'}, 1u,
                           out written, IntPtr.Zero) || written != 1u)
                return "WRITE_ERROR";
            byte[] reply = new byte[2]; uint read;
            if (!ReadFile(handle, reply, 2u, out read, IntPtr.Zero) || read != 2u)
                return "READ_ERROR";
            return System.Text.Encoding.ASCII.GetString(reply);
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
  if ($ProbeB05Package) {
    if ($ExpectedOpen -ne 0 -or -not $B05KeyFile -or
        -not $B05ServiceDll -or -not $B05BinDirectory -or
        $B05KeyFile -notmatch 'DC06R-LAB-' -or
        $B05BinDirectory -notmatch 'DC06R-LAB-') {
      throw 'DC06B05_PACKAGE_PROBE_BOUNDARY'
    }
    # This executes under the real distinct approved Windows account SID,
    # not as administrator and not as LocalService. Only actual Win32
    # ACCESS_DENIED satisfies the contract; missing/locked files do not.
    function Assert-B05AccessDenied([scriptblock]$Attempt,[string]$Code) {
      $wasDenied=$false
      try {
        $stream=& $Attempt
        if ($null -ne $stream) { $stream.Dispose() }
      } catch [System.UnauthorizedAccessException] {
        $wasDenied=$true
      } catch [System.IO.IOException] {
        if ($_.Exception.HResult -eq -2147024891) {
          $wasDenied=$true
        } else {
          throw ('DC06B05_IO_NOT_ACCESS_DENIED_' + $Code)
        }
      }
      if (-not $wasDenied) { throw ('DC06B05_ACCESS_ALLOWED_' + $Code) }
    }
    Assert-B05AccessDenied {
      [System.IO.File]::Open($B05KeyFile,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,[System.IO.FileShare]::ReadWrite)
    } 'KEY_READ'
    Assert-B05AccessDenied {
      [System.IO.File]::Open($B05ServiceDll,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Write,[System.IO.FileShare]::ReadWrite)
    } 'DLL_WRITE'
    Assert-B05AccessDenied {
      [System.IO.File]::Open((Join-Path $B05BinDirectory 'b05-untrusted-drop.tmp'),[System.IO.FileMode]::CreateNew,[System.IO.FileAccess]::Write,[System.IO.FileShare]::None)
    } 'BIN_CREATE'
    Write-Output 'DC06B05_DISTINCT_PIPE_AUTHORIZED_USER_KEY_READ_DLL_WRITE_BIN_CREATE_ALL_DENIED_PASS'
  }
  if ($ProbeQueueReadOnly) {
    if ($ExpectedOpen -ne 0) { throw 'DC06B02_PROBE_NOT_ALLOWED_FOR_DENIED_SID' }
    $reply=[DC06RClient]::ReadOnlyStatus($PipeName)
    if ($reply -ne 85) { throw ('DC06B02_NATIVE_READ_ONLY_STATUS_EXPECT_U_GOT_' + $reply) }
    Write-Output 'DC06B02_NATIVE_SCM_RESTRICTED_SID_READ_ONLY_Q_U_RESPONSE_PASS'
  }
  if ($B03Status -ne 'None') {
    if ($ExpectedOpen -ne 0) { throw 'DC06B03_UNAUTHORIZED_STATUS_PROBE' }
    $actual = [DC06RClient]::B03Status($PipeName)
    # Wrong-key and tampered ciphertext MUST reach the authentication
    # failure E2, not an unrelated ACL/transport fault (E1/E3/E4/E5).
    $expected = if ($B03Status -eq 'Valid') { 'S1' } else { 'E2' }
    $validError = $false
    if ($actual -ne $expected -and -not $validError) {
        throw ('DC06B03_EXPECT_' + $expected + '_GOT_' + $actual)
    }
    Write-Output ('DC06B03_NATIVE_REAL_AES_SPOOL_' +
        $B03Status.ToUpperInvariant() + '_RETURN_' + $actual + '_PASS')
  }
  if ($B06InventoryStatus -ne 'None') {
    if ($B06InventoryStatus -eq 'Unauthorized' -and $ExpectedOpen -ne 5) {
      throw 'DC06_B06_DENIED_USER_EXPECTED'
    }
    if ($B06InventoryStatus -ne 'Unauthorized' -and $ExpectedOpen -ne 0) {
      throw 'DC06_B06_APPROVED_USER_EXPECTED'
    }
    $env:DC06_B06_NATIVE_INVENTORY_LAB='1'
    $python=(Get-Command python -ErrorAction Stop).Source
    & $python -I (Join-Path $PSScriptRoot 'windows_b06_native_inventory_client.py') $PipeName $B06InventoryStatus
    if ($LASTEXITCODE -ne 0) { throw ('DC06_B06_NATIVE_ADAPTER_FAILED_'+$LASTEXITCODE) }
  }
  if ($B06MediaStatus -ne 'None') {
    if ($B06MediaStatus -eq 'Unauthorized' -and $ExpectedOpen -ne 5) {
      throw 'DC06_B06_MEDIA_DENIED_USER_EXPECTED'
    }
    if ($B06MediaStatus -ne 'Unauthorized' -and $ExpectedOpen -ne 0) {
      throw 'DC06_B06_MEDIA_APPROVED_USER_EXPECTED'
    }
    $env:DC06_B06_NATIVE_INVENTORY_LAB='1'
    $env:DC06_B06_NATIVE_MEDIA_LAB='1'
    $python=(Get-Command python -ErrorAction Stop).Source
    & $python -I (Join-Path $PSScriptRoot 'windows_b06_native_media_client.py') $PipeName $B06MediaStatus
    if ($LASTEXITCODE -ne 0) { throw ('DC06_B06_NATIVE_MEDIA_FAILED_'+$LASTEXITCODE) }
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
