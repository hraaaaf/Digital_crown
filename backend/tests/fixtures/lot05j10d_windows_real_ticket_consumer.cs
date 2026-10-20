// LOT05/J10D: SCM-installed, DENY-only verifier of an actual J10C RSA ticket.
// Ticket handoff here is through a CI-protected file, NOT authenticated IPC.
// No clinical code, no import, no restore and no positive authorization result.
using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;

internal sealed class J10DRealTicketConsumer : ServiceBase {
    readonly string[] a;
    J10DRealTicketConsumer(string[] args) { a=args; ServiceName=args[0]; CanStop=true; AutoLog=false; }
    protected override void OnStart(string[] args) {
        new Thread(Inspect) {IsBackground=true}.Start();
    }
    protected override void OnStop() {}

    static bool HasSid(string required) {
        using(var token=WindowsIdentity.GetCurrent()) {
            if(token.Groups==null) return false;
            foreach(IdentityReference group in token.Groups)
                if(string.Equals(group.Value,required,StringComparison.OrdinalIgnoreCase)) return true;
        }
        return false;
    }

    static bool Hex(string value, int chars) {
        if(value==null || value.Length!=chars) return false;
        foreach(char c in value)
            if(!((c>='0' && c<='9')||(c>='a' && c<='f'))) return false;
        return true;
    }

    static bool CheckTicket(string raw, string pin, string owner, string job,
                            string generation, string manifest, out string nonce) {
        nonce="";
        if(raw.Length>2048 || pin.Length>1024) return false;
        var t=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(raw);
        if(t.Count!=3 || !t.ContainsKey("body") || !t.ContainsKey("signature") ||
           !t.ContainsKey("signer_pid") || !(t["body"] is string) ||
           !(t["signature"] is string)) return false;
        string body=(string)t["body"];
        if(body.Length>512 || Encoding.ASCII.GetString(Encoding.ASCII.GetBytes(body))!=body) return false;
        string[] fields=body.Split('|');
        if(fields.Length!=7 || fields[0]!="owner="+owner ||
           fields[1]!="audience=LOT05J10C_SQLCIPHER_FAKE" ||
           fields[2]!="job="+job || fields[3]!="generation="+generation ||
           fields[4]!="manifest="+manifest ||
           !fields[5].StartsWith("nonce=",StringComparison.Ordinal) ||
           !fields[6].StartsWith("expires=",StringComparison.Ordinal)) return false;
        nonce=fields[5].Substring(6);
        if(!Hex(nonce,32)) return false;
        long expiry;
        string v=fields[6].Substring(8);
        if(!long.TryParse(v,out expiry) || expiry.ToString()!=v) return false;
        long now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        if(expiry<=now || expiry>now+90) return false;
        string[] lines=pin.Split(new[]{'\n'},StringSplitOptions.RemoveEmptyEntries);
        if(lines.Length!=3 || lines[2].Trim()!=owner) return false;
        byte[] modulus=Convert.FromBase64String(lines[0].Trim());
        byte[] exponent=Convert.FromBase64String(lines[1].Trim());
        byte[] signature=Convert.FromBase64String((string)t["signature"]);
        if(modulus.Length!=256 || exponent.Length<1 || exponent.Length>8 ||
           signature.Length!=256) return false;
        using(var rsa=new RSACryptoServiceProvider(new CspParameters(24))) {
            rsa.PersistKeyInCsp=false;
            rsa.ImportParameters(new RSAParameters{Modulus=modulus,Exponent=exponent});
            return rsa.VerifyData(Encoding.ASCII.GetBytes(body),
                                  new SHA256CryptoServiceProvider(),signature);
        }
    }

    void Inspect() {
        bool sid=false,verified=false,first=false,replay=false;
        bool hostileRead=false,hostileWrite=false;
        string reason="deny";
        try {
            sid=HasSid(a[8]);
            if(!sid) {
                // Same-account hostile SCM must fail at both independent NTFS ACLs.
                try { File.ReadAllBytes(a[2]); hostileRead=true; } catch(UnauthorizedAccessException) {}
                try { File.WriteAllText(Path.Combine(a[4],"hostile.nonce"),"FORGED"); hostileWrite=true; }
                catch(UnauthorizedAccessException) {}
                reason=hostileRead || hostileWrite ? "sid_denied_acl_bypass" : "sid_denied_acl";
            }
            else {
                string ticket=File.ReadAllText(a[3],new UTF8Encoding(false,true));
                string pin=File.ReadAllText(a[2],Encoding.ASCII);
                string nonce="";
                verified=CheckTicket(ticket,pin,a[5],a[6],a[7],a[9],out nonce);
                if(!verified) reason="signature_or_scope_denied";
                else {
                    var d=new DirectoryInfo(a[4]);
                    if(!d.Exists || (d.Attributes & FileAttributes.ReparsePoint)!=0)
                        reason="ledger_unavailable";
                    else {
                        string marker=Path.Combine(a[4],nonce+".nonce");
                        try {
                            using(var f=new FileStream(marker,FileMode.CreateNew,
                                  FileAccess.Write,FileShare.None,4096,FileOptions.WriteThrough)) {
                                byte[] data=Encoding.ASCII.GetBytes("J10D_DENY_ONLY");
                                f.Write(data,0,data.Length); f.Flush(true);
                            }
                            first=true;
                            reason="signed_once_deny";
                        } catch(IOException) {
                            replay=File.Exists(marker);
                            reason=replay?"replay_denied":"ledger_denied";
                        }
                    }
                }
            }
        } catch(Exception) {reason="fail_closed";}
        // Diagnostic output is not authority and carries no signed body or secrets.
        try {
            File.WriteAllText(a[1],"sid="+sid+"\nverified="+verified+
              "\nfirst="+first+"\nreplay="+replay+"\nhostile_pin_read="+hostileRead+"\nhostile_ledger_write="+hostileWrite+"\nreason="+reason+
              "\nclinical_restore_permitted=False\n",Encoding.ASCII);
        } catch(Exception) {}
    }

    static int Main(string[] args) {
        if(args.Length!=10 || args[0].Length==0 ||
           !args[8].StartsWith("S-1-5-80-",StringComparison.Ordinal)) return 2;
        ServiceBase.Run(new J10DRealTicketConsumer(args));
        return 0;
    }
}
