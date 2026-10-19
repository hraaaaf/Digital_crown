// LOT05.7-J3: ephemeral Windows SCM service test only.
// Compiled exclusively inside an isolated GitHub-hosted Windows CI runner.
// NEVER an application worker, installer, or clinical authority.
using System;
using System.IO;
using System.Security.Principal;
using System.ServiceProcess;

internal sealed class FakeSidProbeService : ServiceBase
{
    private readonly string evidencePath;
    private readonly string protectedFile;
    private readonly string expectedSid;

    private FakeSidProbeService(string serviceName, string evidencePath,
                                string protectedFile, string expectedSid)
    {
        ServiceName = serviceName;
        CanStop = true;
        AutoLog = false;
        this.evidencePath = evidencePath;
        this.protectedFile = protectedFile;
        this.expectedSid = expectedSid;
    }

    private static bool HasSid(string sidText)
    {
        using (WindowsIdentity id = WindowsIdentity.GetCurrent())
        {
            foreach (IdentityReference group in id.Groups)
            {
                if (String.Equals(group.Value, sidText,
                                  StringComparison.OrdinalIgnoreCase))
                    return true;
            }
            return false;
        }
    }

    protected override void OnStart(string[] ignored)
    {
        // No calls to Digital Crown runtime. The probe reads one synthetic file.
        bool tokenHasServiceSid = HasSid(expectedSid);
        bool fileReadable = false;
        string result = "not_attempted";
        try
        {
            string text = File.ReadAllText(protectedFile);
            fileReadable = text == "LOT05J3_FAKE_ONLY";
            result = fileReadable ? "fake_content_ok" : "unexpected_content";
        }
        catch (UnauthorizedAccessException)
        {
            result = "access_denied";
        }
        catch (IOException)
        {
            result = "io_denied";
        }
        using (WindowsIdentity id = WindowsIdentity.GetCurrent())
        {
            string output =
                "identity=" + id.Name + "\n" +
                "target_sid_in_process_token=" + tokenHasServiceSid + "\n" +
                "protected_file_read=" + fileReadable + "\n" +
                "read_result=" + result + "\n";
            // Evidence directory is separately ACL-granted to LocalService.
            File.WriteAllText(evidencePath, output);
        }
    }

    protected override void OnStop() { }

    private static int Main(string[] args)
    {
        if (args.Length == 2 && args[0] == "--probe")
        {
            bool present = HasSid(args[1]);
            Console.WriteLine(present ? "DIRECT_HAS_TARGET_SID" :
                                      "DIRECT_NO_TARGET_SID");
            return present ? 17 : 0;
        }
        if (args.Length != 4)
            return 2;
        ServiceBase.Run(new FakeSidProbeService(args[0], args[1], args[2], args[3]));
        return 0;
    }
}
