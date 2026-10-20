// LOT05/J10D: disposable SCM-only, bounded, deny-only RSA ticket pipe receiver.
// The caller SID authenticates a transport RELAY, not the original J10C issuer.
// No positive authorization, no clinical restore and no product runtime references.
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Security.AccessControl;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;
using System.Threading;
using System.Web.Script.Serialization;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

internal sealed class J10DPipeConsumer : ServiceBase {
    readonly string[] a;
    volatile bool stopping;
    Thread listener;
    J10DPipeConsumer(string[] args) { a=args; ServiceName=args[0]; CanStop=true; AutoLog=false; }
    protected override void OnStart(string[] args) {
        listener=new Thread(Listen) { IsBackground=true };
        listener.Start();
    }
    protected override void OnStop() { stopping=true; }
    static string Deny(string reason) { return "DENY_J10D_"+reason+"\n"; }
    static bool Hex(string value,int length) {
        if(value==null || value.Length!=length) return false;
        foreach(char c in value) if(!((c>='0' && c<='9')||(c>='a' && c<='f'))) return false;
        return true;
    }
    static void ReadExact(NamedPipeServerStream pipe,byte[] b,int at,int total) {
        while(at<total) {
            IAsyncResult task=pipe.BeginRead(b,at,total-at,null,null);
            try {
                if(!task.AsyncWaitHandle.WaitOne(4500)) throw new IOException("timeout");
                int n=pipe.EndRead(task);
                if(n<=0) throw new IOException("closed");
                at+=n;
            } finally {task.AsyncWaitHandle.Close();}
        }
    }
    bool PeerAuthenticated(NamedPipeServerStream pipe) {
        bool matched=false;
        try {
            pipe.RunAsClient(delegate {
                using(var token=WindowsIdentity.GetCurrent(true)) {
                    if(token.Groups==null) return;
                    foreach(IdentityReference group in token.Groups) {
                        if(string.Equals(group.Value,a[2],StringComparison.OrdinalIgnoreCase)) {
                            matched=true; break;
                        }
                    }
                }
            });
        } catch(Exception) {return false;}
        return matched;
    }
    // Laboratory guard: reject reparse points at the pin, ledger or ANY
    // ancestor. This is pathname validation, NOT a handle-anchored NTFS
    // TOCTOU or protection against an Administrator with WRITE_DAC.
    static bool PlainPath(string path,bool directory) {
        string full=Path.GetFullPath(path);
        if(!directory &&
           (File.GetAttributes(full) & FileAttributes.ReparsePoint)!=0) return false;
        string cursor=directory ? full : Path.GetDirectoryName(full);
        while(!string.IsNullOrEmpty(cursor)) {
            FileAttributes attrs=File.GetAttributes(cursor);
            if((attrs & FileAttributes.Directory)==0 ||
               (attrs & FileAttributes.ReparsePoint)!=0) return false;
            string parent=Path.GetDirectoryName(cursor.TrimEnd(
                Path.DirectorySeparatorChar,Path.AltDirectorySeparatorChar));
            if(string.IsNullOrEmpty(parent) || parent==cursor) break;
            cursor=parent;
        }
        return true;
    }
    // The consumer's own SID, SYSTEM and Administrators are the *only*
    // direct allow ACE identities. Admin remains explicitly in the threat
    // model of the laboratory fixture, not an independently trusted root.
    static bool ExactConsumerAcl(FileSystemSecurity security,string consumerSid) {
        if(!security.AreAccessRulesProtected) return false;
        var accepted=new HashSet<string>(StringComparer.OrdinalIgnoreCase) {
            consumerSid,"S-1-5-18","S-1-5-32-544"
        };
        var found=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var rules=security.GetAccessRules(true,false,typeof(SecurityIdentifier));
        foreach(AuthorizationRule item in rules) {
            var rule=item as FileSystemAccessRule;
            if(rule==null || rule.AccessControlType!=AccessControlType.Allow ||
               !accepted.Contains(rule.IdentityReference.Value) ||
               !found.Add(rule.IdentityReference.Value)) return false;
        }
        return found.SetEquals(accepted);
    }
    // J10D test-only Win32/NT handle-relative nonce: opening a child relative
    // to an ALREADY OPENED directory cannot be redirected by replacing its
    // path between the directory check and FILE_CREATE.
    // This DOES NOT prevent privileged rollback before handle acquisition,
    // restore of both trust data and nonce ledger, or crash/powerloss issues.
    const uint FILE_READ_ATTRIBUTES = 0x80;
    const uint FILE_LIST_DIRECTORY = 0x1;
    const uint SYNCHRONIZE = 0x00100000;
    const uint GENERIC_WRITE = 0x40000000;
    const uint FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;
    const uint FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000;
    const uint FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400;
    const uint FILE_ATTRIBUTE_DIRECTORY = 0x00000010;
    const uint FILE_CREATE = 2;
    const uint FILE_NON_DIRECTORY_FILE = 0x40;
    const uint FILE_SYNCHRONOUS_IO_NONALERT = 0x20;
    const uint FILE_WRITE_THROUGH = 0x2;
    const int STATUS_OBJECT_NAME_COLLISION = unchecked((int)0xC0000035);

    [StructLayout(LayoutKind.Sequential)]
    struct UnicodeName {
        public ushort Length;
        public ushort MaximumLength;
        public IntPtr Buffer;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct ObjectAttributes {
        public uint Length;
        public IntPtr RootDirectory;
        public IntPtr ObjectName;
        public uint Attributes;
        public IntPtr SecurityDescriptor;
        public IntPtr SecurityQualityOfService;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct IoStatus {
        public IntPtr Status;
        public IntPtr Information;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct ByHandleInfo {
        public uint Attributes;
        public uint CreationLow,CreationHigh;
        public uint AccessLow,AccessHigh;
        public uint WriteLow,WriteHigh;
        public uint VolumeSerial,SizeHigh,SizeLow,Links,FileIndexHigh,FileIndexLow;
    }
    [DllImport("kernel32.dll",EntryPoint="CreateFileW",CharSet=CharSet.Unicode,
        SetLastError=true)]
    static extern SafeFileHandle OpenDirectory(string path,uint access,
        uint share,IntPtr security,uint disposition,uint flags,IntPtr template);
    [DllImport("kernel32.dll",SetLastError=true)]
    [return:MarshalAs(UnmanagedType.Bool)]
    static extern bool GetFileInformationByHandle(SafeFileHandle handle,out ByHandleInfo info);
    [DllImport("ntdll.dll",ExactSpelling=true)]
    static extern int NtCreateFile(out SafeFileHandle handle,uint access,
        ref ObjectAttributes attributes,out IoStatus io,IntPtr allocation,
        uint fileAttributes,uint share,uint disposition,uint options,
        IntPtr ea,uint eaLength);

    static SafeFileHandle OpenLedgerHandle(string path) {
        SafeFileHandle directory=OpenDirectory(path,
            FILE_READ_ATTRIBUTES|FILE_LIST_DIRECTORY|SYNCHRONIZE,
            1|2|4,IntPtr.Zero,3,
            FILE_FLAG_BACKUP_SEMANTICS|FILE_FLAG_OPEN_REPARSE_POINT,
            IntPtr.Zero);
        if(directory==null || directory.IsInvalid) {
            if(directory!=null) directory.Dispose();
            throw new IOException("deny directory open");
        }
        ByHandleInfo metadata;
        if(!GetFileInformationByHandle(directory,out metadata) ||
           (metadata.Attributes & FILE_ATTRIBUTE_DIRECTORY)==0 ||
           (metadata.Attributes & FILE_ATTRIBUTE_REPARSE_POINT)!=0) {
            directory.Dispose();
            throw new IOException("deny reparse directory handle");
        }
        return directory;
    }

    static string BurnNonceRelative(SafeFileHandle directory,string nonce) {
        if(!Hex(nonce,32)) return Deny("LEDGER_INVALID");
        // This UnicodeName contains only a fixed hex basename. No separators,
        // drive prefix, colon, parent path, slash or user-controlled component.
        string leaf=nonce+".nonce";
        var unicode=new UnicodeName();
        unicode.Buffer=Marshal.StringToHGlobalUni(leaf);
        unicode.Length=(ushort)(leaf.Length*2);
        unicode.MaximumLength=(ushort)((leaf.Length+1)*2);
        IntPtr name=IntPtr.Zero;
        SafeFileHandle marker=null;
        try {
            name=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(UnicodeName)));
            Marshal.StructureToPtr(unicode,name,false);
            var attributes=new ObjectAttributes {
                Length=(uint)Marshal.SizeOf(typeof(ObjectAttributes)),
                RootDirectory=directory.DangerousGetHandle(),
                ObjectName=name,
                Attributes=0x40 /* OBJ_CASE_INSENSITIVE */
            };
            IoStatus io;
            int status=NtCreateFile(out marker,GENERIC_WRITE|SYNCHRONIZE,
                ref attributes,out io,IntPtr.Zero,0,1,FILE_CREATE,
                FILE_NON_DIRECTORY_FILE|FILE_SYNCHRONOUS_IO_NONALERT|
                    FILE_WRITE_THROUGH|FILE_FLAG_OPEN_REPARSE_POINT,
                IntPtr.Zero,0);
            if(status==STATUS_OBJECT_NAME_COLLISION)
                return Deny("NONCE_REPLAY_OR_LEDGER");
            if(status<0 || marker==null || marker.IsInvalid)
                return Deny("LEDGER_INVALID");
            using(var stream=new FileStream(marker,FileAccess.Write,4096,false)) {
                marker=null; // FileStream owns this SafeFileHandle.
                byte[] payload=Encoding.ASCII.GetBytes("J10D_PIPE_DENY_ONLY");
                stream.Write(payload,0,payload.Length);
                stream.Flush(true);
            }
            return Deny("RSA_VERIFIED_NONCE_BURNED");
        } catch(Exception) {return Deny("LEDGER_INVALID");}
        finally {
            if(marker!=null) marker.Dispose();
            if(name!=IntPtr.Zero) Marshal.FreeHGlobal(name);
            if(unicode.Buffer!=IntPtr.Zero) Marshal.FreeHGlobal(unicode.Buffer);
        }
    }

    bool Verify(string json,out string nonce) {
        nonce="";
        if(json.Length>2048 || json.Length<1) return false;
        var ticket=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(json);
        if(ticket.Count!=3 || !ticket.ContainsKey("body") || !ticket.ContainsKey("signature") ||
           !ticket.ContainsKey("signer_pid") || !(ticket["body"] is string) ||
           !(ticket["signature"] is string)) return false;
        string body=(string)ticket["body"];
        if(body.Length>512 || Encoding.ASCII.GetString(Encoding.ASCII.GetBytes(body))!=body)
            return false;
        string[] parts=body.Split('|');
        if(parts.Length!=7 || parts[0]!="owner="+a[6] ||
           parts[1]!="audience=LOT05J10C_SQLCIPHER_FAKE" ||
           parts[2]!="job="+a[7] || parts[3]!="generation="+a[8] ||
           parts[4]!="manifest="+a[9] || !parts[5].StartsWith("nonce=",StringComparison.Ordinal) ||
           !parts[6].StartsWith("expires=",StringComparison.Ordinal)) return false;
        nonce=parts[5].Substring(6);
        if(!Hex(nonce,32)) return false;
        string expire=parts[6].Substring(8);
        long expiry;
        if(!long.TryParse(expire,out expiry) || expiry.ToString()!=expire) return false;
        long now=DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        if(expiry<=now || expiry>now+90) return false;
        // A J10C signature with an attacker-substituted public pin does not
        // establish publisher provenance. Enforce only SCM fixture ACL here.
        if(!PlainPath(a[4],false) ||
           !ExactConsumerAcl(File.GetAccessControl(a[4]),a[3])) return false;
        var lines=File.ReadAllLines(a[4],Encoding.ASCII);
        if(lines.Length!=3 || lines[2]!=a[6]) return false;
        byte[] mod=Convert.FromBase64String(lines[0]);
        byte[] exp=Convert.FromBase64String(lines[1]);
        byte[] sig=Convert.FromBase64String((string)ticket["signature"]);
        if(mod.Length!=256 || exp.Length==0 || exp.Length>8 || sig.Length!=256) return false;
        using(var rsa=new RSACryptoServiceProvider(new CspParameters(24))) {
            rsa.PersistKeyInCsp=false;
            rsa.ImportParameters(new RSAParameters {Modulus=mod,Exponent=exp});
            return rsa.VerifyData(Encoding.ASCII.GetBytes(body),
                new SHA256CryptoServiceProvider(),sig);
        }
    }
    string Validate(byte[] raw) {
        try {
            string json=new UTF8Encoding(false,true).GetString(raw);
            string nonce="";
            if(!Verify(json,out nonce)) return Deny("SIGNATURE_OR_SCOPE");
            var folder=new DirectoryInfo(a[5]);
            if(!folder.Exists || !PlainPath(a[5],true) ||
               !ExactConsumerAcl(Directory.GetAccessControl(a[5]),a[3]))
                return Deny("LEDGER_INVALID");
            // Critical ordering: reparse/ACL checks -> no-follow OPEN DIRECTORY
            // -> create child RELATIVE TO THE SAME DIRECTORY HANDLE. A path
            // rename/swap after opening cannot redirect that child create.
            using(SafeFileHandle directory=OpenLedgerHandle(a[5]))
                return BurnNonceRelative(directory,nonce);
        } catch(Exception) {return Deny("FAIL_CLOSED");}
    }
    void Listen() {
        while(!stopping) {
            try {
                var acl=new PipeSecurity();
                acl.SetAccessRuleProtection(true,false);
                acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(a[2]),
                    PipeAccessRights.ReadWrite,AccessControlType.Allow));
                acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(a[3]),
                    PipeAccessRights.FullControl,AccessControlType.Allow));
                acl.AddAccessRule(new PipeAccessRule(new SecurityIdentifier(WellKnownSidType.LocalSystemSid,null),
                    PipeAccessRights.FullControl,AccessControlType.Allow));
                using(var pipe=new NamedPipeServerStream(a[1],PipeDirection.InOut,1,
                    PipeTransmissionMode.Byte,PipeOptions.Asynchronous,4096,4096,acl)) {
                    IAsyncResult pending=pipe.BeginWaitForConnection(null,null);
                    try {
                        while(!stopping && !pending.AsyncWaitHandle.WaitOne(150)) {}
                        if(stopping) return;
                        pipe.EndWaitForConnection(pending);
                    } finally {pending.AsyncWaitHandle.Close();}
                    var head=new byte[3];
                    ReadExact(pipe,head,0,3);
                    int n=(head[1]<<8)|head[2];
                    string response=Deny("FRAME");
                    if(head[0]==(byte)'J' && n>0 && n<=2048) {
                        var frame=new byte[n];
                        ReadExact(pipe,frame,0,n);
                        response=PeerAuthenticated(pipe) ? Validate(frame) : Deny("PEER");
                    }
                    var bytes=Encoding.ASCII.GetBytes(response);
                    pipe.Write(bytes,0,bytes.Length);
                    pipe.Flush();
                }
            } catch(Exception) {
                if(stopping) return;
                Thread.Sleep(120);
            }
        }
    }
    static int Main(string[] args) {
        if(args.Length!=10 || args[0].Length==0 || args[1].Length==0 ||
           !args[2].StartsWith("S-1-5-80-",StringComparison.Ordinal) ||
           !args[3].StartsWith("S-1-5-80-",StringComparison.Ordinal)) return 2;
        ServiceBase.Run(new J10DPipeConsumer(args));
        return 0;
    }
}
