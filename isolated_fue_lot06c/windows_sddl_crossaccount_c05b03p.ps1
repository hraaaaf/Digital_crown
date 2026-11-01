#Requires -Version 7.0
# C05B-03P: disposable Win32 pipe with custom SDDL + real alternate Windows user.
# CI ephemeral local user is deleted in finally. It is NOT an installed service.
# The denial probe uses genuine Windows LogonUser + RunImpersonated token;
# it is a cross-ACCOUNT token test, NOT cross-process hostile-user evidence.
$ErrorActionPreference = 'Stop'
if (-not $IsWindows -or $env:ENVIRONMENT -ne 'test' -or
    $env:DIGITALCROWN_ISOLATED_RUNTIME -ne 'true') {
    throw 'C05B03P_WINDOWS_ISOLATED_TEST_ONLY'
}
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Principal;
using Microsoft.Win32.SafeHandles;
public static class DC06PSddlProbe {
    [StructLayout(LayoutKind.Sequential)]
    public struct SecurityAttributes {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public int bInheritHandle;
    }

    [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    public static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(
        string sddl, uint revision, out IntPtr descriptor, out uint size);
    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern IntPtr LocalFree(IntPtr descriptor);

    [DllImport("kernel32.dll", EntryPoint="CreateNamedPipeW", CharSet=CharSet.Unicode,
        SetLastError=true)]
    public static extern SafeFileHandle CreateNamedPipe(
        string name, uint openMode, uint pipeMode, uint instances,
        uint outSize, uint inSize, uint timeout, ref SecurityAttributes attrs);

    [DllImport("kernel32.dll", EntryPoint="CreateFileW", CharSet=CharSet.Unicode,
        SetLastError=true)]
    public static extern SafeFileHandle CreateFile(
        string name, uint access, uint shareMode, IntPtr security,
        uint disposition, uint flags, IntPtr template);

    [DllImport("advapi32.dll", EntryPoint="LogonUserW", CharSet=CharSet.Unicode,
        SetLastError=true)]
    public static extern bool LogonUser(string user, string domain, string password,
        int type, int provider, out SafeAccessTokenHandle token);

    private const uint PIPE_ACCESS_DUPLEX = 3;
    private const uint FILE_FLAG_FIRST_PIPE_INSTANCE = 0x00080000;
    private const uint FILE_FLAG_OVERLAPPED = 0x40000000;
    private const uint PIPE_REJECT_REMOTE_CLIENTS = 0x00000008;

    // The exact policy flags are passed to native CreateNamedPipeW below.
    public static SafeFileHandle OpenFirstServer(string path, string sddl) {
        IntPtr descriptor = IntPtr.Zero;
        uint size;
        if (!ConvertStringSecurityDescriptorToSecurityDescriptor(sddl, 1, out descriptor, out size))
            throw new Win32Exception(Marshal.GetLastWin32Error(), "C05B03P_INVALID_SDDL");
        try {
            var attrs = new SecurityAttributes {
                nLength = Marshal.SizeOf<SecurityAttributes>(),
                lpSecurityDescriptor = descriptor, bInheritHandle = 0
            };
            SafeFileHandle pipe = CreateNamedPipe(
                path, PIPE_ACCESS_DUPLEX | FILE_FLAG_FIRST_PIPE_INSTANCE |
                    FILE_FLAG_OVERLAPPED,
                PIPE_REJECT_REMOTE_CLIENTS, 1, 4096, 4096, 5000, ref attrs);
            if (pipe.IsInvalid) {
                int error = Marshal.GetLastWin32Error();
                pipe.Dispose();
                throw new Win32Exception(error, "C05B03P_NATIVE_PIPE_CREATE_FAILED");
            }
            return pipe;
        }
        finally {
            if (descriptor != IntPtr.Zero) LocalFree(descriptor);
        }
    }

    public static int FirstInstanceDuplicateError(string path, string sddl) {
        try {
            using (var unexpected = OpenFirstServer(path, sddl)) { return 0; }
        } catch (Win32Exception e) { return e.NativeErrorCode; }
    }

    public static int OpenLocalClient(string path) {
        using (var handle = CreateFile(path, 0xC0000000u, 0, IntPtr.Zero, 3, 0, IntPtr.Zero)) {
            return handle.IsInvalid ? Marshal.GetLastWin32Error() : 0;
        }
    }

    public static SafeAccessTokenHandle ObtainDifferentLocalAccount(
        string user, string password) {
        SafeAccessTokenHandle token;
        if (!LogonUser(user, ".", password, 2, 0, out token))
            throw new Win32Exception(Marshal.GetLastWin32Error(),
                "C05B03P_CANNOT_LOGON_UNPRIVILEGED_TEST_ACCOUNT");
        return token;
    }

    public static int ProbeDeniedUnderRealToken(
        SafeAccessTokenHandle token, string pipe, string expectedSid) {
        int errorCode = -1;
        string actualSid = "";
        WindowsIdentity.RunImpersonated(token, () => {
            using (var who = WindowsIdentity.GetCurrent(true)) {
                actualSid = who.User.Value;
                errorCode = OpenLocalClient(pipe);
            }
        });
        if (!String.Equals(actualSid, expectedSid, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("C05B03P_WRONG_ALTERNATE_OS_TOKEN");
        return errorCode;
    }
}
'@
$name = 'dc06p' + [Guid]::NewGuid().ToString('N').Substring(0,9)
$password = 'Xy9!' + [Guid]::NewGuid().ToString('N') + '!aA'
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$pipeName = '\\.\pipe\DigitalCrown-LOT06-P-' + [Guid]::NewGuid().ToString('N')
$pipe = $null
$testUserCreated = $false
$token = $null
try {
    $serverSid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    New-LocalUser -Name $name -Password $securePassword -Description (
        'Disposable CI C05B03P negative DACL identity'
    ) -ErrorAction Stop | Out-Null
    $testUserCreated = $true
    $other = Get-LocalUser -Name $name -ErrorAction Stop
    $otherSid = $other.SID.Value
    if ($otherSid -eq $serverSid) { throw 'C05B03P_NOT_A_DISTINCT_USER' }

    # Protect DACL (D:P); only current test server Windows SID and SYSTEM have GA.
    # No Everyone, BUILTIN Users, Anonymous, or alternate account ACE.
    $sddl = 'D:P(A;;GA;;;' + $serverSid + ')(A;;GA;;;SY)'
    $pipe = [DC06PSddlProbe]::OpenFirstServer($pipeName, $sddl)
    $duplicateCode = [DC06PSddlProbe]::FirstInstanceDuplicateError($pipeName, $sddl)
    if ($duplicateCode -ne 5) {
        throw ('C05B03P_FIRST_INSTANCE_HIJACK_NOT_BLOCKED_WIN32_' + $duplicateCode)
    }
    Write-Output 'C05B03P_WIN32_SDDL_FIRST_INSTANCE_REMOTE_REJECT_FLAG_PASS'

    $token = [DC06PSddlProbe]::ObtainDifferentLocalAccount($name, $password)
    $deniedCode = [DC06PSddlProbe]::ProbeDeniedUnderRealToken(
        $token, $pipeName, $otherSid
    )
    if ($deniedCode -ne 5) {
        throw ('C05B03P_CROSS_ACCOUNT_OPEN_NOT_ACCESS_DENIED_' + $deniedCode)
    }
    Write-Output 'C05B03P_REAL_DIFFERENT_LOCAL_USER_TOKEN_ACCESS_DENIED_5_PASS'

    # Attempt the allowed caller only after denied caller: no busy-pipe false denial.
    $allowed = [DC06PSddlProbe]::OpenLocalClient($pipeName)
    if ($allowed -ne 0) {
        throw ('C05B03P_APPROVED_USER_CANNOT_OPEN_' + $allowed)
    }
    Write-Output 'C05B03P_APPROVED_SAME_ACCOUNT_CLIENT_OPEN_PASS'
    Write-Output 'C05B03P_NOT_AN_SCM_SERVICE_SID_OR_REAL_REMOTE_PROBE'
}
finally {
    if ($null -ne $token) { $token.Dispose() }
    if ($null -ne $pipe) { $pipe.Dispose() }
    if ($testUserCreated) {
        Remove-LocalUser -Name $name -ErrorAction Stop
    }
    $password = $null
    $securePassword = $null
}
