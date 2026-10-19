// LOT05.7-J9: Disposable real Windows Service SID signer and unprivileged key-reader.
// No imported production code, no clinical content or restoration.
using System;
using System.Diagnostics;
using System.IO;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;
internal sealed class J9SignerService : ServiceBase {
    readonly string[] a;
    J9SignerService(string[] args) { a=args; ServiceName=args[0]; AutoLog=false; CanStop=true; }
    static bool HasSid(string sid) {
        using(var identity=WindowsIdentity.GetCurrent()) {
            foreach(IdentityReference group in identity.Groups)
                if(string.Equals(group.Value,sid,StringComparison.OrdinalIgnoreCase)) return true;
        }
        return false;
    }
    protected override void OnStart(string[] args) { new Thread(Run) {IsBackground=true}.Start(); }
    void Run() {
        string mode=a[1], report=a[2], key=a[3], config=a[4],
               request=a[5], output=a[6], py=a[7], repo=a[8], requiredSid=a[9];
        bool sid=HasSid(requiredSid), privateReadable=false, configReadable=false, issued=false;
        bool requestReadable=false, privateWritable=false, configWritable=false;
        bool requestWritable=false, issuedOutputWritable=false;
        string reason="not_started";
        try {
            if(mode=="attacker") {
                // The separate SCM instance has the SAME LocalService account,
                // but not the signer's real SCM Service SID. Perform genuine
                // OS file attempts, not mocked ACL predicates.
                try { File.ReadAllBytes(key); privateReadable=true; } catch(UnauthorizedAccessException) { }
                try { File.ReadAllBytes(config); configReadable=true; } catch(UnauthorizedAccessException) { }
                try { File.ReadAllBytes(request); requestReadable=true; } catch(UnauthorizedAccessException) { }
                try { File.WriteAllText(key,"J9_FAKE_CLIENT_CORRUPTION"); privateWritable=true; } catch(UnauthorizedAccessException) { }
                try { File.WriteAllText(config,"J9_FAKE_CLIENT_CORRUPTION"); configWritable=true; } catch(UnauthorizedAccessException) { }
                try { File.WriteAllText(request,"J9_FAKE_CLIENT_CORRUPTION"); requestWritable=true; } catch(UnauthorizedAccessException) { }
                // Attempt to pre-create/overwrite the signer output with an
                // unsigned fake object. A writable telemetry file is NOT
                // acceptable as the signer-to-worker handoff authority.
                try { File.WriteAllText(output,"J9_FAKE_FORGED_TICKET"); issuedOutputWritable=true; } catch(UnauthorizedAccessException) { }
                reason=(!sid && !privateReadable && !configReadable && !requestReadable &&
                       !privateWritable && !configWritable && !requestWritable &&
                       !issuedOutputWritable) ? "client_access_denied" : "ATTACK_BYPASS";
            } else if(mode=="sign" && sid) {
                var start=new ProcessStartInfo {
                    FileName=py, Arguments="-B -m backend.tests.fixtures.lot05j9_real_jwt_rsa_signer_lab \""+Path.GetDirectoryName(key)+"\"",
                    WorkingDirectory=repo, UseShellExecute=false, CreateNoWindow=true,
                    RedirectStandardInput=true, RedirectStandardOutput=true, RedirectStandardError=true
                };
                start.EnvironmentVariables["PYTHONPATH"]=repo;
                start.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"]="1";
                start.EnvironmentVariables["LOT05J9_REAL_JWT_SCM_FAKE_ONLY"]="1";
                start.EnvironmentVariables["LOT05E_REAL_SQLCIPHER_FAKE_ONLY"]="1";
                start.EnvironmentVariables["LOT05I_REAL_JWT_WAL_FAKE_ONLY"]="1";
                start.EnvironmentVariables["ENVIRONMENT"]="cabinet";
                foreach(string entry in File.ReadAllLines(config)) {
                    int sep=entry.IndexOf('=');
                    if(sep<1) throw new IOException("invalid test config");
                    string k=entry.Substring(0,sep);
                    if(k!="DATABASE_URL" && k!="SQLCIPHER_KEY_HEX" && k!="SECRET_KEY" && k!="CABINET_MASTER_KEY_HEX")
                        throw new IOException("unsupported test config");
                    start.EnvironmentVariables[k]=entry.Substring(sep+1);
                }
                using(var child=new Process()) {
                    child.StartInfo=start;
                    child.Start();
                    child.StandardInput.Write(File.ReadAllText(request,Encoding.UTF8));
                    child.StandardInput.Close();
                    string result=child.StandardOutput.ReadToEnd();
                    string stderr=child.StandardError.ReadToEnd();
                    if(!child.WaitForExit(90000)) { child.Kill(); throw new IOException("signer timeout"); }
                    if(child.ExitCode==0 && result.Contains("\"signature\"") && result.Contains("LOT05J9_FAKE_WORKER")) {
                        File.WriteAllText(output,result,Encoding.UTF8);
                        issued=true;
                        reason="authenticated_jwt_signed";
                    } else {
                        // Only sanitized error CATEGORY; no token, path or key is logged.
                        // J9_DENIED_* also covers SQLCipher/setup errors: it is NOT
                        // evidence of a JWT failure without HTTP_401 evidence.
                        reason=stderr.Contains("J9_DENIED_HTTP_401") ? "jwt_http_401" :
                               stderr.Contains("J9_DENIED_HTTP_403") ? "jwt_http_403" :
                               stderr.Contains("J9_DENIED_J8Denied") ? "preauth_guard_denied" :
                               stderr.Contains("J9_DENIED_") ? "signer_other_denied" : "fail_closed";
                    }
                }
            } else reason="invalid_mode_or_sid";
        } catch(Exception ex) {
            // No JWT, private key, SQLCipher key or unsafe exception payloads in reports.
            reason="DENY_"+ex.GetType().Name;
        }
        using(var identity=WindowsIdentity.GetCurrent()) {
            File.WriteAllText(report,
              "identity="+identity.Name+"\nservice_sid_in_token="+sid+
              "\nclient_private_read="+privateReadable+"\nclient_config_read="+configReadable+
              "\nclient_request_read="+requestReadable+
              "\nclient_private_write="+privateWritable+
              "\nclient_config_write="+configWritable+
              "\nclient_request_write="+requestWritable+
              "\nclient_output_forge="+issuedOutputWritable+
              "\nticket_issued="+issued+"\nreason="+reason+"\n");
        }
    }
    protected override void OnStop() {}
    static int Main(string[] args) {
        if(args.Length!=10) return 2;
        ServiceBase.Run(new J9SignerService(args));
        return 0;
    }
}