// LOT05/J10D: actual disposable SCM LocalService authenticated-pipe RELAY.
// It forwards a J10C-issued test ticket; NOT the JWT/RSA issuer service itself.
// No secrets are sent to logs and no clinical action exists.
using System;
using System.IO;
using System.IO.Pipes;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;

internal sealed class J10DTicketRelay : ServiceBase {
    readonly string[] a;
    J10DTicketRelay(string[] args) {a=args;ServiceName=args[0];CanStop=true;AutoLog=false;}
    protected override void OnStart(string[] args) {new Thread(Send){IsBackground=true}.Start();}
    protected override void OnStop() {}
    static bool HasSid(string sid) {
        using(var token=WindowsIdentity.GetCurrent()) {
            if(token.Groups==null) return false;
            foreach(IdentityReference g in token.Groups)
                if(string.Equals(g.Value,sid,StringComparison.OrdinalIgnoreCase)) return true;
        }
        return false;
    }
    void Send() {
        bool sid=HasSid(a[4]);
        string response="DENY_J10D_TRANSPORT";
        for(int i=0;i<24;i++) {
            try {
                using(var pipe=new NamedPipeClientStream(".",a[1],PipeDirection.InOut,
                    PipeOptions.None,TokenImpersonationLevel.Impersonation)) {
                    pipe.Connect(400);
                    byte[] raw=File.ReadAllBytes(a[2]);
                    if(raw.Length==0 || raw.Length>2048) {
                        response="DENY_J10D_BAD_FRAME";break;
                    }
                    pipe.ReadTimeout=6000;pipe.WriteTimeout=6000;
                    pipe.WriteByte((byte)'J');
                    pipe.WriteByte((byte)(raw.Length>>8));
                    pipe.WriteByte((byte)(raw.Length&255));
                    pipe.Write(raw,0,raw.Length);
                    pipe.Flush();
                    byte[] ack=new byte[96];
                    int n=pipe.Read(ack,0,ack.Length);
                    string data=Encoding.ASCII.GetString(ack,0,n).Trim();
                    response=data.StartsWith("DENY_J10D_",StringComparison.Ordinal)?
                        data : "DENY_J10D_INVALID_SERVER";
                    break;
                }
            } catch(UnauthorizedAccessException) {
                response="DENY_PIPE_ACCESS";break;
            } catch(TimeoutException) {Thread.Sleep(180);}
              catch(IOException) {Thread.Sleep(180);}
              catch(Exception) {response="DENY_J10D_EXCEPTION";break;}
        }
        try {File.WriteAllText(a[3],"service_sid_present="+sid+"\nresponse="+response+"\n",Encoding.ASCII);}
        catch(Exception) {}
    }
    static int Main(string[] args) {
        if(args.Length!=5 || args[0].Length==0 || args[1].Length==0 ||
           !args[4].StartsWith("S-1-5-80-",StringComparison.Ordinal)) return 2;
        ServiceBase.Run(new J10DTicketRelay(args));return 0;
    }
}
