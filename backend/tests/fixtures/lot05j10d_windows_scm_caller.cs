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
    private Thread thread;
    J10DCaller(string name,string pipe,string evidence) {
        ServiceName=name; pipeName=pipe; evidencePath=evidence;
        CanStop=true; AutoLog=false;
    }
    protected override void OnStart(string[] args) {
        thread=new Thread(Probe) {IsBackground=true};
        thread.Start();
    }
    private void Probe() {
        string outcome="FAIL";
        for(int attempt=0;attempt<30;attempt++) {
            try {
                using(var pipe=new NamedPipeClientStream(".",pipeName,PipeDirection.InOut,
                    PipeOptions.None,TokenImpersonationLevel.Impersonation)) {
                    pipe.Connect(400);
                    var buffer=new byte[64];
                    int n=pipe.Read(buffer,0,buffer.Length);
                    string response=Encoding.ASCII.GetString(buffer,0,n);
                    outcome=response=="DENY_J10D_UNATTESTED\n" ? "DENY_FROM_PIPE" : "FAIL_BAD_RESPONSE";
                    break;
                }
            } catch(System.TimeoutException) { Thread.Sleep(200); }
              catch(UnauthorizedAccessException) { outcome="FAIL_ACCESS_DENIED"; break; }
              catch(IOException) { Thread.Sleep(200); }
              catch(Exception) { outcome="FAIL_EXCEPTION"; break; }
        }
        try { File.WriteAllText(evidencePath,outcome); } catch(Exception) {}
    }
    static int Main(string[] args) {
        if(args.Length!=3) return 2;
        ServiceBase.Run(new J10DCaller(args[0],args[1],args[2]));
        return 0;
    }
}
