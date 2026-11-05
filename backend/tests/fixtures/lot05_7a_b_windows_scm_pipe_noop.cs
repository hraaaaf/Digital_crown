// LOT05.7A-B: real Windows SCM ServiceBase + authenticated named pipe.
// EPHEMERAL CI LAB ONLY. No signer keys, SQL, clinical IO, product installation.
using System;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;

internal sealed class NoopScmPipeService : ServiceBase
{
    private readonly string pipeName;
    private readonly string expectedClientSid;
    private readonly string requiredServiceSid;
    private readonly string proofFile;
    private readonly int connections;

    private NoopScmPipeService(string serviceName, string pipeName,
        string expectedClientSid, string requiredServiceSid,
        string proofFile, int connections)
    {
        ServiceName = serviceName;
        CanStop = true;
        AutoLog = false;
        this.pipeName = pipeName;
        this.expectedClientSid = expectedClientSid;
        this.requiredServiceSid = requiredServiceSid;
        this.proofFile = proofFile;
        this.connections = connections;
    }

    private static bool HasTokenServiceSid(string requiredSid)
    {
        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
        {
            foreach (IdentityReference group in identity.Groups)
                if (String.Equals(group.Value, requiredSid, StringComparison.OrdinalIgnoreCase))
                    return true;
            return false;
        }
    }

    private static string BoundedLine(Stream pipe)
    {
        var bytes = new byte[129];
        for (int i = 0; i < bytes.Length; i++)
        {
            int current = pipe.ReadByte();
            if (current < 0) return "DENIED_TRUNCATED";
            if (current == 10)
                return Encoding.ASCII.GetString(bytes, 0, i);
            bytes[i] = (byte)current;
        }
        return "DENIED_OVERSIZE";
    }

    private static PipeSecurity RestrictPipe(string callerSid, string serviceSid)
    {
        PipeSecurity acl = new PipeSecurity();
        acl.SetAccessRuleProtection(true, false);
        acl.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(serviceSid), PipeAccessRights.FullControl, AccessControlType.Allow));
        acl.AddAccessRule(new PipeAccessRule(
            new SecurityIdentifier(callerSid), PipeAccessRights.ReadWrite, AccessControlType.Allow));
        // No Everyone, Users or Anonymous grant.
        return acl;
    }

    private void Serve()
    {
        bool serviceSidInToken = HasTokenServiceSid(requiredServiceSid);
        try
        {
            if (!serviceSidInToken) throw new UnauthorizedAccessException("SERVICE_SID_MISMATCH");
            PipeSecurity acl = RestrictPipe(expectedClientSid, requiredServiceSid);
            for (int index = 0; index < connections; index++)
            {
                using (NamedPipeServerStream pipe = new NamedPipeServerStream(
                    pipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte,
                    PipeOptions.None, 256, 256, acl))
                {
                    if (index == 0) File.AppendAllText(proofFile, "READY=YES\n");
                    pipe.WaitForConnection();
                    string observedSid = "";
                    pipe.RunAsClient(delegate()
                    {
                        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
                            observedSid = identity.User.Value;
                    });
                    string request = BoundedLine(pipe);
                    bool peerMatch = String.Equals(observedSid, expectedClientSid,
                                                  StringComparison.OrdinalIgnoreCase);
                    string reply = !peerMatch ? "DENY_PEER" :
                                   request == "SYNTHETIC_NOOP_V1" ? "NOOP_VERIFIED_NO_CLINICAL_IMPORT" :
                                   "DENY_SCHEMA";
                    byte[] response = Encoding.ASCII.GetBytes(reply + "\n");
                    pipe.Write(response, 0, response.Length);
                    pipe.Flush();
                    File.AppendAllText(proofFile, "SERVICE_SID_PRESENT=" + serviceSidInToken +
                        " PEER_FROM_OS=" + observedSid + " PEER_MATCH=" + peerMatch +
                        " RESPONSE=" + reply + "\n");
                }
            }
        }
        catch (Exception exception)
        {
            File.AppendAllText(proofFile, "DENY_SERVER_ERROR=" + exception.GetType().Name + "\n");
        }
    }

    protected override void OnStart(string[] args)
    {
        Thread worker = new Thread(Serve);
        worker.IsBackground = true;
        worker.Start();
    }
    protected override void OnStop() { }

    private static int Main(string[] args)
    {
        if (args.Length != 6 || args[1].Length > 96 ||
            !args[1].StartsWith("dc05b_", StringComparison.Ordinal) ||
            (args[5] != "1" && args[5] != "3")) return 2;
        ServiceBase.Run(new NoopScmPipeService(
            args[0], args[1], args[2], args[3], args[4], Int32.Parse(args[5])));
        return 0;
    }
}
