// LOT06 C05B-03R: disposable test-only Windows SCM service, NEVER product code.
// Build/run ONLY on GitHub-hosted Windows runner. No patient data, network or keys.
using Microsoft.Win32.SafeHandles;
using System.ComponentModel;
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

    static readonly ManualResetEventSlim StopRequested = new(false);
    static ServiceMainDelegate? s_main;
    static HandlerDelegate? s_handler;
    static IntPtr s_statusHandle;
    static SafeFileHandle? s_pipe;
    static string s_name = "";
    static string s_pipeName = "";
    static string s_serviceSid = "";
    static string s_clientSid = "";
    static int s_state = SERVICE_START_PENDING;

    static int Main(string[] args)
    {
        if (args.Length != 5 || args[0] != "--service" ||
            !args[1].StartsWith("DC06R", StringComparison.Ordinal) ||
            !args[2].StartsWith(@"\\.\pipe\DigitalCrown-LAB-R-", StringComparison.Ordinal) ||
            !args[3].StartsWith("S-1-5-80-", StringComparison.Ordinal) ||
            !args[4].StartsWith("S-1-5-21-", StringComparison.Ordinal))
            return 35;
        (s_name, s_pipeName, s_serviceSid, s_clientSid) =
            (args[1], args[2], args[3], args[4]);
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
                       ")(A;;0x00100003;;;" + s_clientSid + ")(A;;GA;;;SY)";
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
                _ = ReadFile(pipe, buffer, 1, out _, IntPtr.Zero);
                _ = DisconnectNamedPipe(pipe);
            }
            catch (ObjectDisposedException) { break; }
            catch { break; }
        }
    }
}
