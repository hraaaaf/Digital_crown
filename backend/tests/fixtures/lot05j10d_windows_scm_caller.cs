// LOT05/J10D laboratory-only second SCM service. Never signs or authorizes.
using System;
using System.IO;
using System.IO.Pipes;
using System.ServiceProcess;
using System.Security.Principal;
using System.Text;
using System.Threading;

internal sealed class J10DCaller : ServiceBase {
    private readonly string pipeName;
    private readonly string evidencePath;
    private readonly string forbiddenProbePath;
    private Thread thread;
    J10DCaller(string name,string pipe,string evidence,string forbidden) {
        ServiceName=name; pipeName=pipe; evidencePath=evidence;
        forbiddenProbePath=forbidden;
        CanStop=true; AutoLog=false;
    }
    protected override void OnStart(string[] args) {
        thread=new Thread(Probe) {IsBackground=true};
        thread.Start();
    }
    private void Probe() {
        string outcome="FAIL";
        string isolation="";
        if(!string.IsNullOrEmpty(forbiddenProbePath)) {
            // Third service uses the SAME LocalService account but a different
            // SCM Service SID. It must not be able to forge caller evidence.
            try { File.WriteAllText(forbiddenProbePath,"J10D_HOSTILE_FORGERY"); isolation="FORGED"; }
            catch(UnauthorizedAccessException) { isolation="WRITE_DENIED"; }
            catch(Exception) { isolation="WRITE_ERROR"; }
        }
        for(int attempt=0;attempt<30;attempt++) {
            try {
                using(var pipe=new NamedPipeClientStream(".",pipeName,PipeDirection.InOut,
                    PipeOptions.None,TokenImpersonationLevel.Impersonation)) {
                    pipe.Connect(400);
                    pipe.WriteByte((byte)'P');
                    pipe.Flush();
                    var buffer=new byte[64];
                    int n=pipe.Read(buffer,0,buffer.Length);
                    string response=Encoding.ASCII.GetString(buffer,0,n);
                    outcome=response=="DENY_J10D_SID_PRESENT\\n" ? "DENY_SID_PROVEN" : "FAIL_BAD_RESPONSE";
                    break;
                }
            } catch(System.TimeoutException) { Thread.Sleep(200); }
              catch(UnauthorizedAccessException) { outcome="FAIL_ACCESS_DENIED"; break; }
              catch(IOException) { Thread.Sleep(200); }
              catch(Exception) { outcome="FAIL_EXCEPTION"; break; }
        }
        try { File.WriteAllText(evidencePath,outcome+isolation); } catch(Exception) {}
    }
    static int Main(string[] args) {
        if(args.Length!=3 && args.Length!=4) return 2;
        ServiceBase.Run(new J10DCaller(args[0],args[1],args[2],
            args.Length==4 ? args[3] : null));
        return 0;
    }
}
