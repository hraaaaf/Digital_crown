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
    // This is a negative identity probe, never an authorization decision.
    // RunAsClient impersonates the connected pipe peer while reading its token.
    // A service SID must be present and enabled; a generic account name is
    // insufficient. Even a matching SID never permits a restore.
    private bool InspectPeerServiceSid(NamedPipeServerStream pipe) {
        bool matched=false;
        try {
            pipe.RunAsClient(delegate {
                using(var identity=WindowsIdentity.GetCurrent(true)) {
                    var expected=new SecurityIdentifier(allowedSignerSid);
                    var groups=identity.Groups;
                    if(groups==null) return;
                    foreach(IdentityReference group in groups) {
                        var sid=group as SecurityIdentifier;
                        if(sid!=null && sid.Equals(expected)) { matched=true; break; }
                    }
                }
            });
        } catch(Exception) {
            return false;
        }
        return matched;
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
                    // Probe the actual peer token, not the claimed JSON identity.
                    // This result is intentionally NOT used to grant authority.
                    bool peerServiceSidPresent=InspectPeerServiceSid(pipe);
                    if(peerServiceSidPresent) {
                        // A matching token alone cannot authorize any operation.
                    }
                    // Mandatory fail-closed: no independent trust anchor, nonce
                    // ledger, signer binding or restore verification exists.
                    // Every request remains denied, including matching peers.
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
