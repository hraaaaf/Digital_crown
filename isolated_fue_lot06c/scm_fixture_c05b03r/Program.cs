// LOT06 C05B-03R: disposable test-only Windows SCM service, NEVER product code.
// Build/run ONLY on GitHub-hosted Windows runner. No patient data, network or keys.
using Microsoft.Win32.SafeHandles;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Principal;

internal static class Program
{
    const int SERVICE_WIN32_OWN_PROCESS = 0x10;
    const int SERVICE_STOPPED = 1;
    const int SERVICE_START_PENDING = 2;
    const int SERVICE_STOP_PENDING = 3;
    const int SERVICE_RUNNING = 4;
    const int SERVICE_ACCEPT_STOP = 1;
    const int SERVICE_CONTROL_STOP = 1;
    const int ERROR_PIPE_CONNECTED = 535;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct ServiceTableEntry
    {
        [MarshalAs(UnmanagedType.LPWStr)] public string? Name;
        [MarshalAs(UnmanagedType.FunctionPtr)] public ServiceMainDelegate? Main;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct ServiceStatus
    {
        public int Type, State, Controls, Win32Exit, ServiceSpecificExit, CheckPoint, WaitHint;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct SecurityAttributes
    {
        public int Length;
        public IntPtr Descriptor;
        public int Inherit;
    }

    delegate void ServiceMainDelegate(int argc, IntPtr argv);
    delegate uint HandlerDelegate(int control, uint eventType, IntPtr data, IntPtr context);

    [DllImport("advapi32.dll", EntryPoint = "StartServiceCtrlDispatcherW",
        CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool StartDispatcher([In] ServiceTableEntry[] table);

    [DllImport("advapi32.dll", EntryPoint = "RegisterServiceCtrlHandlerExW",
        CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr RegisterHandler(string name, HandlerDelegate handler, IntPtr context);

    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool SetServiceStatus(IntPtr handle, ref ServiceStatus status);

    [DllImport("advapi32.dll", EntryPoint = "ConvertStringSecurityDescriptorToSecurityDescriptorW",
        CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool ConvertSddl(string sddl, uint revision,
        out IntPtr descriptor, out uint length);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr LocalFree(IntPtr descriptor);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool FlushFileBuffers(SafeFileHandle handle);

    [DllImport("kernel32.dll", EntryPoint = "CreateNamedPipeW",
        CharSet = CharSet.Unicode, SetLastError = true)]
    static extern SafeFileHandle CreatePipe(string path, uint openMode, uint mode,
        uint instances, uint outSize, uint inSize, uint timeout, ref SecurityAttributes attrs);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool ConnectNamedPipe(SafeFileHandle pipe, IntPtr overlapped);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool DisconnectNamedPipe(SafeFileHandle pipe);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool ReadFile(SafeFileHandle pipe,
        [Out] byte[] buffer, uint nBytes, out uint bytes, IntPtr overlapped);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool WriteFile(SafeFileHandle pipe,
        byte[] buffer, uint nBytes, out uint written, IntPtr overlapped);

    // B02 Q->U is only a native IPC liveness/refusal probe.
    // U = unassigned queue NOT exposed over this pipe, clinical NO-GO.
    // It grants no patient identity, media access, signing key or receipt.
    static readonly ManualResetEventSlim StopRequested = new(false);
    static ServiceMainDelegate? s_main;
    static HandlerDelegate? s_handler;
    static IntPtr s_statusHandle;
    static SafeFileHandle? s_pipe;
    static string s_name = "";
    static string s_pipeName = "";
    static string s_serviceSid = "";
    static string s_clientSid = "";
    static string? s_b03Python, s_b03Script, s_b03Watch, s_b03Private, s_b03Key;
    static int s_state = SERVICE_START_PENDING;

    static int Main(string[] args)
    {
        if ((args.Length != 5 && args.Length != 11) || args[0] != "--service" ||
            !args[1].StartsWith("DC06R", StringComparison.Ordinal) ||
            !args[2].StartsWith(@"\\.\pipe\DigitalCrown-LAB-R-", StringComparison.Ordinal) ||
            !args[3].StartsWith("S-1-5-80-", StringComparison.Ordinal) ||
            !args[4].StartsWith("S-1-5-21-", StringComparison.Ordinal))
            return 35;
        (s_name, s_pipeName, s_serviceSid, s_clientSid) =
            (args[1], args[2], args[3], args[4]);
        if (args.Length == 11)
        {
            if (args[5] != "--b03-spool" || !Path.IsPathFullyQualified(args[6]) ||
                !Path.IsPathFullyQualified(args[7]) || !Path.IsPathFullyQualified(args[8]) ||
                !Path.IsPathFullyQualified(args[9]) || !Path.IsPathFullyQualified(args[10]) ||
                !args[9].Contains("DC06R-LAB-", StringComparison.OrdinalIgnoreCase) ||
                !File.Exists(args[7]) || !File.Exists(args[10]))
                return 36;
            (s_b03Python, s_b03Script, s_b03Watch, s_b03Private, s_b03Key) =
                (args[6], args[7], args[8], args[9], args[10]);
        }
        s_main = ServiceMain;
        var entries = new ServiceTableEntry[2];
        entries[0] = new ServiceTableEntry { Name = s_name, Main = s_main };
        entries[1] = new ServiceTableEntry { Name = null, Main = null };
        return StartDispatcher(entries) ? 0 : Marshal.GetLastWin32Error();
    }

    static void Report(int state, int win32Exit = 0)
    {
        s_state = state;
        var status = new ServiceStatus
        {
            Type = SERVICE_WIN32_OWN_PROCESS,
            State = state,
            Controls = state == SERVICE_RUNNING ? SERVICE_ACCEPT_STOP : 0,
            Win32Exit = win32Exit,
            WaitHint = state == SERVICE_START_PENDING || state == SERVICE_STOP_PENDING ? 10000 : 0,
            CheckPoint = state == SERVICE_START_PENDING || state == SERVICE_STOP_PENDING ? 1 : 0
        };
        if (s_statusHandle != IntPtr.Zero && !SetServiceStatus(s_statusHandle, ref status))
            throw new Win32Exception(Marshal.GetLastWin32Error(), "C05B03R_STATUS");
    }

    static uint OnControl(int control, uint eventType, IntPtr data, IntPtr context)
    {
        if (control == SERVICE_CONTROL_STOP)
        {
            StopRequested.Set();
            // Closing the server handle allows blocking accept/read to unwind.
            s_pipe?.Dispose();
            try { Report(SERVICE_STOP_PENDING); } catch { /* SCM teardown */ }
        }
        return 0;
    }

    static void ServiceMain(int argc, IntPtr argv)
    {
        s_handler = OnControl;
        s_statusHandle = RegisterHandler(s_name, s_handler, IntPtr.Zero);
        if (s_statusHandle == IntPtr.Zero) return;
        try
        {
            Report(SERVICE_START_PENDING);
            using var identity = WindowsIdentity.GetCurrent();
            if (identity.User is null || identity.User.Value != "S-1-5-19")
                throw new InvalidOperationException("C05B03R_SERVICE_NOT_LOCAL_SERVICE");
            // Check *live* service process access-token groups, not sc showsid text.
            if (identity.Groups is null ||
                !identity.Groups.Cast<IdentityReference>()
                    .Any(group => group.Value == s_serviceSid))
                throw new InvalidOperationException("C05B03R_SERVICE_SID_NOT_IN_LIVE_PROCESS_TOKEN");

            var sddl = "D:P(A;;GA;;;" + s_serviceSid +
                       ")(A;;0x00100183;;;" + s_clientSid + ")(A;;GA;;;SY)";
            IntPtr descriptor = IntPtr.Zero;
            if (!ConvertSddl(sddl, 1, out descriptor, out _))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "C05B03R_SDDL_FAILED");
            try
            {
                var attrs = new SecurityAttributes
                {
                    Length = Marshal.SizeOf<SecurityAttributes>(),
                    Descriptor = descriptor, Inherit = 0
                };
                // FILE_FLAG_FIRST_PIPE_INSTANCE plus PIPE_REJECT_REMOTE_CLIENTS.
                s_pipe = CreatePipe(s_pipeName, 3u | 0x00080000u,
                    0x00000008u, 4, 4096, 4096, 5000, ref attrs);
                if (s_pipe.IsInvalid)
                    throw new Win32Exception(Marshal.GetLastWin32Error(), "C05B03R_PIPE_FAILED");
            }
            finally { if (descriptor != IntPtr.Zero) LocalFree(descriptor); }
            Report(SERVICE_RUNNING); // SCM now confirms identity + native pipe.
            var worker = new Thread(Serve) { IsBackground = true };
            worker.Start();
            StopRequested.Wait(TimeSpan.FromMinutes(3)); // hard lab bound
            s_pipe.Dispose();
            worker.Join(TimeSpan.FromSeconds(3));
            Report(SERVICE_STOPPED);
        }
        catch
        {
            try { Report(SERVICE_STOPPED, 1); } catch { /* no UI or patient logs */ }
            s_pipe?.Dispose();
        }
    }

    static byte[] ReadVerifiedUnassignedCount()
    {
        // This is a disposable lab service under LocalService, reading the
        // REAL AES-GCM/SQLite spool via a fixed Python helper as its own token.
        // Never forward file bytes, patient identity, key or encrypted metadata.
        if (s_b03Python is null || s_b03Script is null || s_b03Watch is null ||
            s_b03Private is null || s_b03Key is null)
            return new byte[] { (byte)'E', (byte)'?' };
        try
        {
            var start = new ProcessStartInfo(s_b03Python) {
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true,
            };
            foreach (var arg in new[] {
                "-I", s_b03Script, "read", s_b03Watch, s_b03Private, s_b03Key, "DC06B03_SYNTHETIC_ONLY"
            }) start.ArgumentList.Add(arg);
            start.Environment["PYTHONDONTWRITEBYTECODE"] = "1";
            using var child = Process.Start(start);
            if (child is null) return new byte[] { (byte)'E', (byte)'5' };
            if (!child.WaitForExit(8000))
            {
                child.Kill(entireProcessTree: true);
                return new byte[] { (byte)'E', (byte)'4' };
            }
            var result = child.StandardOutput.ReadToEnd();
            // LAB-only no-PHI classification of access/integrity/launch failures.
            if (child.ExitCode != 0)
            {
                if (result.Length == 2 && result[0] == 'E' &&
                    ((result[1] >= '1' && result[1] <= '4') ||
                     (result[1] >= 'A' && result[1] <= 'Z')))
                    return new byte[] { (byte)'E', (byte)result[1] };
                return new byte[] { (byte)'E', (byte)'3' };
            }
            if (result.Length != 2 || result[0] != 'S' ||
                result[1] < '0' || result[1] > '9')
                return new byte[] { (byte)'E', (byte)'3' };
            return new byte[] { (byte)'S', (byte)result[1] };
        }
        catch { return new byte[] { (byte)'E', (byte)'5' }; }
    }

    static byte[] ReadVerifiedUnassignedInventory()
    {
        // B06: LocalService decrypts/verifies the pending capture using the
        // SAME AES-GCM/SQLite source; sends metadata only, never image or PHI.
        // LAB only; neither pipe ACL nor this frame is clinical device trust.
        static byte[] Refused() => new byte[] { (byte)'E', (byte)'2' };
        if (s_b03Python is null || s_b03Script is null || s_b03Watch is null ||
            s_b03Private is null || s_b03Key is null)
            return Refused();
        try
        {
            var start = new ProcessStartInfo(s_b03Python) {
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true,
            };
            foreach (var arg in new[] {
                "-I", s_b03Script, "inventory", s_b03Watch, s_b03Private,
                s_b03Key, "DC06B03_SYNTHETIC_ONLY"
            }) start.ArgumentList.Add(arg);
            start.Environment["PYTHONDONTWRITEBYTECODE"] = "1";
            using var child = Process.Start(start);
            if (child is null) return Refused();
            if (!child.WaitForExit(8000)) {
                child.Kill(entireProcessTree: true);
                return Refused();
            }
            if (child.ExitCode != 0) return Refused();
            using var bytes = new MemoryStream();
            child.StandardOutput.BaseStream.CopyTo(bytes);
            var response = bytes.ToArray();
            if (response.Length == 2 && response[0] == (byte)'N' &&
                response[1] == (byte)'0')
                return response;
            if (response.Length != 86 || response[0] != (byte)'I' ||
                response[1] != (byte)'1')
                return Refused();
            for (var i = 2; i < 20; ++i)
                if (response[i] < (byte)'0' || response[i] > (byte)'9')
                    return Refused();
            for (var i = 20; i < 84; ++i)
                if (!((response[i] >= (byte)'0' && response[i] <= (byte)'9') ||
                    (response[i] >= (byte)'a' && response[i] <= (byte)'f')))
                    return Refused();
            if (response[84] != (byte)'P' && response[84] != (byte)'J' &&
                response[84] != (byte)'W' && response[84] != (byte)'D')
                return Refused();
            if (response[85] != (byte)'P' && response[85] != (byte)'R')
                return Refused();
            return response;
        }
        catch { return Refused(); }
    }

    static byte[] ReadVerifiedMediaSlice(byte[] request)
    {
        // Explicit synthetic LAB-only binary media. Restricted Win32 pipe SID
        // is NOT a production operator/session authorization.
        static byte[] Refused() => new byte[] {
            (byte)'E', (byte)'0', (byte)'0', (byte)'0', (byte)'0'
        };
        if (request.Length != 86 || s_b03Python is null || s_b03Script is null ||
            s_b03Watch is null || s_b03Private is null || s_b03Key is null)
            return Refused();
        for (var i = 0; i < 10; ++i)
            if (request[i] < (byte)'0' || request[i] > (byte)'9') return Refused();
        for (var i = 10; i < 74; ++i)
            if (!((request[i] >= (byte)'0' && request[i] <= (byte)'9') ||
                (request[i] >= (byte)'a' && request[i] <= (byte)'f')))
                return Refused();
        for (var i = 74; i < 86; ++i)
            if (request[i] < (byte)'0' || request[i] > (byte)'9') return Refused();
        var id = System.Text.Encoding.ASCII.GetString(request, 0, 10);
        var digest = System.Text.Encoding.ASCII.GetString(request, 10, 64);
        var offsetText = System.Text.Encoding.ASCII.GetString(request, 74, 8);
        var countText = System.Text.Encoding.ASCII.GetString(request, 82, 4);
        if (!ulong.TryParse(id, out var item) || item == 0 ||
            !int.TryParse(offsetText, out var offset) ||
            !int.TryParse(countText, out var count) ||
            offset < 0 || count < 1 || count > 2048 ||
            offset + count > 16384) return Refused();

        try
        {
            var start = new ProcessStartInfo(s_b03Python) {
                UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardOutput = true, RedirectStandardError = true,
            };
            foreach (var arg in new[] {
                "-I", s_b03Script, "media", s_b03Watch, s_b03Private, s_b03Key,
                "DC06B03_SYNTHETIC_ONLY", id, digest, offsetText, countText
            }) start.ArgumentList.Add(arg);
            start.Environment["PYTHONDONTWRITEBYTECODE"] = "1";
            using var child = Process.Start(start);
            if (child is null) return Refused();
            if (!child.WaitForExit(8000)) {
                child.Kill(entireProcessTree: true);
                return Refused();
            }
            if (child.ExitCode != 0) return Refused();
            using var bytes = new MemoryStream();
            child.StandardOutput.BaseStream.CopyTo(bytes);
            var response = bytes.ToArray();
            if (response.Length != count + 5 || response[0] != (byte)'D')
                return Refused();
            for (var i = 1; i <= 4; ++i)
                if (response[i] < (byte)'0' || response[i] > (byte)'9')
                    return Refused();
            var sizeText = System.Text.Encoding.ASCII.GetString(response, 1, 4);
            return int.TryParse(sizeText, out var actual) && actual == count
                ? response : Refused();
        }
        catch { return Refused(); }
    }

    static void Serve()
    {
        var pipe = s_pipe;
        if (pipe is null) return;
        while (!StopRequested.IsSet)
        {
            try
            {
                if (!ConnectNamedPipe(pipe, IntPtr.Zero) &&
                    Marshal.GetLastWin32Error() != ERROR_PIPE_CONNECTED)
                    break;
                var buffer = new byte[1];
                var readOk = ReadFile(pipe, buffer, 1, out uint received, IntPtr.Zero);
                if (readOk && received == 1 && buffer[0] == (byte)'Q')
                {
                    var response = new byte[] { (byte)'U' };
                    if (!WriteFile(pipe, response, 1, out uint written, IntPtr.Zero)
                        || written != 1)
                        throw new InvalidOperationException("DC06_BS2_Q_REPLY_WRITE_FAILED");
                    // The client must consume 'U' BEFORE DisconnectNamedPipe:
                    // Windows drops unread pipe bytes on disconnect. Unlike
                    // a delay, FlushFileBuffers provides an OS-backed drain
                    // boundary for this synchronous, disposable lab fixture.
                    if (!FlushFileBuffers(pipe))
                        throw new InvalidOperationException("DC06_BS2_Q_REPLY_DRAIN_FAILED");
                }
                else if (readOk && received == 1 && buffer[0] == (byte)'S')
                {
                    var response = ReadVerifiedUnassignedCount();
                    _ = WriteFile(pipe, response, 2, out _, IntPtr.Zero);
                }
                else if (readOk && received == 1 && buffer[0] == (byte)'I')
                {
                    var response = ReadVerifiedUnassignedInventory();
                    _ = WriteFile(pipe, response, (uint)response.Length, out _, IntPtr.Zero);
                }
                else if (readOk && received == 1 && buffer[0] == (byte)'M')
                {
                    var request = new byte[86];
                    uint total = 0;
                    while (total < 86)
                    {
                        var part = new byte[86 - (int)total];
                        if (!ReadFile(pipe, part, (uint)part.Length, out uint got, IntPtr.Zero) ||
                            got == 0) break;
                        Array.Copy(part, 0, request, (int)total, got);
                        total += got;
                    }
                    var response = total == 86 ? ReadVerifiedMediaSlice(request)
                        : new byte[] { (byte)'E', (byte)'0', (byte)'0', (byte)'0', (byte)'0' };
                    // The byte-mode pipe must remain connected until the client
                    // has drained the entire binary reply; disconnecting directly
                    // after WriteFile can discard unread bytes (notably the PNG).
                    // LAB peer closes on denied replies; the service is one-shot,
                    // disposable and never installed in a clinical workstation.
                    if (WriteFile(pipe, response, (uint)response.Length,
                                  out uint sent, IntPtr.Zero) &&
                        sent == (uint)response.Length)
                    {
                        var drained = new byte[1];
                        _ = ReadFile(pipe, drained, 1, out _, IntPtr.Zero);
                    }
                }
                else if (readOk && received == 1 && buffer[0] != (byte)'R')
                {
                    // Preserve the pre-B03 one-way 'R' probe: it closes its
                    // handle after sending and MUST NOT receive a reply.
                    var denied = new byte[] { (byte)'E', (byte)'?' };
                    _ = WriteFile(pipe, denied, 2, out _, IntPtr.Zero);
                }
                _ = DisconnectNamedPipe(pipe);
            }
            catch (ObjectDisposedException) { break; }
            catch { break; }
        }
    }
}
