// LOT05/J10D: standalone, independently installable SCM *DENY-ONLY* pipe consumer.
// Proof scaffold, not authenticated restore IPC. Never opens a clinical database.
using System;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Principal;
using System.ServiceProcess;
using System.Threading;

internal sealed class J10DConsumer : ServiceBase {
    private readonly string pipeName;
    private readonly string allowedSignerSid;
    private Thread thread;
    private volatile bool stopping;

    J10DConsumer(string serviceName, string pipeName, string signerSid) {
        ServiceName=serviceName; CanStop=true; AutoLog=false;
        this.pipeName=pipeName; allowedSignerSid=signerSid;
    }
    protected override void OnStart(string[] args) {
        stopping=false;
        thread=new Thread(Listen) { IsBackground=true };
        thread.Start();
    }
    private void Listen() {
        while(!stopping) {
            try {
                var acl=new PipeSecurity();
                var system=new SecurityIdentifier(WellKnownSidType.LocalSystemSid,null);
                var signer=new SecurityIdentifier(allowedSignerSid);
                // The pipe's access-control list is explicitly restricted to
                // SYSTEM and the caller service SID; no Everyone/LocalService ACE.
                acl.SetAccessRuleProtection(true,false);
                acl.AddAccessRule(new PipeAccessRule(system,PipeAccessRights.FullControl,AccessControlType.Allow));
                acl.AddAccessRule(new PipeAccessRule(signer,PipeAccessRights.ReadWrite,AccessControlType.Allow));
                using(var pipe=new NamedPipeServerStream(pipeName,PipeDirection.InOut,1,
                    PipeTransmissionMode.Byte,PipeOptions.Asynchronous,1024,1024,acl)) {
                    IAsyncResult wait=pipe.BeginWaitForConnection(null,null);
                    while(!stopping && !wait.AsyncWaitHandle.WaitOne(200)) {}
                    if(stopping) return;
                    pipe.EndWaitForConnection(wait);
                    // Mandatory fail-closed: the ACL is only a first boundary.
                    // No client impersonation/token check, nonce ledger or signature
                    // verification is implemented. Always reject every request.
                    byte[] denied=System.Text.Encoding.ASCII.GetBytes("DENY_J10D_UNATTESTED\n");
                    pipe.Write(denied,0,denied.Length);
                    pipe.Flush();
                }
            } catch(Exception) {
                // Service must never turn a pipe failure into authorization.
                if(stopping) return;
                Thread.Sleep(250);
            }
        }
    }
    protected override void OnStop() { stopping=true; }
    static int Main(string[] args) {
        if(args.Length!=3) return 2;
        if(args[0].Length==0 || args[1].Length==0 || !args[2].StartsWith("S-1-5-80-",StringComparison.Ordinal)) return 3;
        ServiceBase.Run(new J10DConsumer(args[0],args[1],args[2]));
        return 0;
    }
}
