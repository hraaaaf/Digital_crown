// LOT05.7A-C: ephemeral SCM named pipe -> child Ed25519 verifier lab.
// No product installer, no private signer in service, no clinical import, no DB.
// The service accepts ONLY synthetic NOOP if BOTH the Windows peer token and
// independently checked signed claims match fixture-only provisioned context.
using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;

internal sealed class SignedNoopPipeService : ServiceBase
{
    private readonly string pipeName, allowedSid, expectedPeerSid, serviceSid;
    private readonly string proofFile, pythonExe, configFile, ledgerDir, verifierModule;
    private readonly int connectionCount;

    private SignedNoopPipeService(string name, string pipe, string allowedSid, string expectedPeerSid,
        string serviceSid, string proof, string pythonExe, string configFile, string ledgerDir,
        string verifierModule, int connectionCount)
    {
        ServiceName = name; CanStop = true; AutoLog = false;
        this.pipeName = pipe; this.allowedSid = allowedSid; this.expectedPeerSid = expectedPeerSid;
        this.serviceSid = serviceSid; this.proofFile = proof;
        this.pythonExe = pythonExe; this.configFile = configFile;
        this.ledgerDir = ledgerDir; this.verifierModule = verifierModule;
        this.connectionCount = connectionCount;
    }

    private bool HasServiceSid()
    {
        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
        {
            foreach (IdentityReference group in identity.Groups)
                if (String.Equals(group.Value, serviceSid, StringComparison.OrdinalIgnoreCase))
                    return true;
        }
        return false;
    }

    private PipeSecurity PipeAcl()
    {
        PipeSecurity acl = new PipeSecurity();
        acl.SetAccessRuleProtection(true, false);
        acl.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(serviceSid), PipeAccessRights.FullControl, AccessControlType.Allow));
        acl.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(allowedSid), PipeAccessRights.ReadWrite, AccessControlType.Allow));
        return acl; // No Everyone, Users, Anonymous or general LocalService ACL
    }

    private static string ReadBoundedAscii(Stream pipe)
    {
        byte[] buffer = new byte[8193];
        for (int n = 0; n < buffer.Length; n++)
        {
            int next = pipe.ReadByte();
            if (next == -1) return "";
            if (next == 10) return Encoding.ASCII.GetString(buffer, 0, n);
            if (next < 32 || next > 126) return "";
            buffer[n] = (byte)next;
        }
        return "";
    }

    private static string Quote(string value) { return "\"" + value.Replace("\"", "") + "\""; }

    private bool DetachedVerifierAllows(string request)
    {
        if (String.IsNullOrEmpty(request) || request.Length > 8192) return false;
        ProcessStartInfo info = new ProcessStartInfo(pythonExe,
            "-B " + Quote(verifierModule) + " " + Quote(configFile) + " " +
            Quote(ledgerDir) + " " + Quote(verifierModule));
        info.UseShellExecute = false;
        info.CreateNoWindow = true;
        info.RedirectStandardInput = true;
        info.RedirectStandardOutput = true;
        info.RedirectStandardError = false;
        info.EnvironmentVariables["LOT05_7A_C_FAKE_ONLY"] = "1";
        try
        {
            using (Process child = Process.Start(info))
            {
                if (child == null) return false;
                child.StandardInput.WriteLine(request);
                child.StandardInput.Flush();
                child.StandardInput.Close();
                if (!child.WaitForExit(5000))
                {
                    try { child.Kill(); } catch (InvalidOperationException) { }
                    return false;
                }
                string response = child.StandardOutput.ReadToEnd().Trim();
                return child.ExitCode == 0 && response == "ALLOW_SYNTHETIC_NOOP_ONLY";
            }
        }
        catch (Exception) { return false; }
    }

    private void Serve()
    {
        try
        {
            if (!HasServiceSid()) throw new UnauthorizedAccessException("SERVICE_SID_MISMATCH");
            PipeSecurity acl = PipeAcl();
            for (int i = 0; i < connectionCount; i++)
            {
                using (var pipe = new NamedPipeServerStream(pipeName, PipeDirection.InOut, 1,
                    PipeTransmissionMode.Byte, PipeOptions.None, 1024, 1024, acl))
                {
                    if (i == 0) File.AppendAllText(proofFile, "READY=YES\n");
                    pipe.WaitForConnection();
                    string observedPeerSid = "";
                    pipe.RunAsClient(delegate()
                    {
                        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
                            observedPeerSid = identity.User.Value;
                    });
                    bool peerMatches = String.Equals(observedPeerSid, expectedPeerSid,
                        StringComparison.OrdinalIgnoreCase);
                    string request = ReadBoundedAscii(pipe);
                    string reply = peerMatches && DetachedVerifierAllows(request)
                        ? "NOOP_SIGNED_VERIFIED_NO_CLINICAL_IMPORT" : "DENY";
                    byte[] bytes = Encoding.ASCII.GetBytes(reply + "\n");
                    pipe.Write(bytes, 0, bytes.Length);
                    pipe.Flush();
                    File.AppendAllText(proofFile, "SERVICE_SID_PRESENT=True" +
                        " PEER_SID_FROM_OS=" + observedPeerSid +
                        " PEER_MATCH=" + peerMatches + " RESPONSE=" + reply + "\n");
                }
            }
        }
        catch (Exception exception)
        {
            File.AppendAllText(proofFile, "DENY_SERVICE_ERROR=" + exception.GetType().Name + "\n");
        }
    }

    protected override void OnStart(string[] ignored)
    {
        Thread worker = new Thread(Serve);
        worker.IsBackground = true;
        worker.Start();
    }
    protected override void OnStop() { }

    private static int Main(string[] args)
    {
        if (args.Length != 11 || args[1].Length > 96 ||
            !args[1].StartsWith("dc05c_", StringComparison.Ordinal) ||
            (args[10] != "1" && args[10] != "10")) return 2;
        ServiceBase.Run(new SignedNoopPipeService(args[0],args[1],args[2],args[3],args[4],
            args[5],args[6],args[7],args[8],args[9],Int32.Parse(args[10])));
        return 0;
    }
}
