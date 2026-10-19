// LOT05.7-J9: actual Windows SCM ServiceBase consumes detached JWT-authorized signed ticket, FAKE only.
// NO imports from clinical runtime, NO patient files, NO restore operation.
using System;
using System.IO;
using System.Security.Cryptography;
using System.Security.Principal;
using System.ServiceProcess;
using System.Text;

internal sealed class FakePinnedKeyWorker : ServiceBase
{
    private readonly string evidence, publicKey, signedJob, forgedJob, requiredSid, ledger;

    private FakePinnedKeyWorker(string name, string evidence, string publicKey,
                                string signedJob, string forgedJob,
                                string requiredSid, string ledger)
    {
        ServiceName = name;
        CanStop = true;
        AutoLog = false;
        this.evidence = evidence;
        this.publicKey = publicKey;
        this.signedJob = signedJob;
        this.forgedJob = forgedJob;
        this.requiredSid = requiredSid;
        this.ledger = ledger;
    }

    private static bool HasServiceSid(string sid)
    {
        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
        {
            foreach (IdentityReference group in identity.Groups)
                if (String.Equals(group.Value, sid, StringComparison.OrdinalIgnoreCase))
                    return true;
        }
        return false;
    }

    private static bool ValidBody(string data, string expectedOwner, out string nonce)
    {
        nonce = "";
        string[] segments = data.Split('|');
        if (segments.Length != 4 || segments[0] != "owner=" + expectedOwner ||
            segments[1] != "audience=LOT05J9_FAKE_WORKER" ||
            !segments[2].StartsWith("nonce=", StringComparison.Ordinal) ||
            !segments[3].StartsWith("expires=", StringComparison.Ordinal))
            return false;
        nonce = segments[2].Substring(6);
        if (nonce.Length != 32) return false;
        foreach (char ch in nonce)
            if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'f')))
                return false;
        long expiry;
        if (!long.TryParse(segments[3].Substring(8), out expiry)) return false;
        long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        return expiry > now && expiry <= now + 120;
    }

    private static bool Verify(byte[] modulus, byte[] exponent,
                               string expectedOwner, string[] lines, out string nonce)
    {
        nonce = "";
        if (lines.Length != 2 || modulus.Length != 256 || exponent.Length == 0
            || exponent.Length > 8 || !ValidBody(lines[0], expectedOwner, out nonce))
            return false;
        try
        {
            RSAParameters parameter = new RSAParameters {
                Modulus = modulus, Exponent = exponent
            };
            using (RSACryptoServiceProvider rsa = new RSACryptoServiceProvider(new CspParameters(24)))
            {
                rsa.PersistKeyInCsp = false;
                rsa.ImportParameters(parameter);
                byte[] signature = Convert.FromBase64String(lines[1]);
                return rsa.VerifyData(Encoding.UTF8.GetBytes(lines[0]),
                                      new SHA256CryptoServiceProvider(), signature);
            }
        }
        catch (CryptographicException) { return false; }
        catch (FormatException) { return false; }
    }

    protected override void OnStart(string[] ignored)
    {
        bool hasSid = HasServiceSid(requiredSid);
        bool publicRead = false, valid = false, tamperDenied = false;
        bool firstUse = false, replayDenied = false;
        string reason = "not_attempted";
        try
        {
            string[] publicLines = File.ReadAllLines(publicKey, Encoding.ASCII);
            if (publicLines.Length != 3) throw new IOException("FAKE_PUBLIC_KEY_FORMAT");
            int ownerId;
            if (!int.TryParse(publicLines[2], out ownerId) || ownerId <= 0 ||
                publicLines[2] != ownerId.ToString()) throw new IOException("FAKE_PINNED_OWNER_INVALID");
            string expectedOwner = publicLines[2];
            byte[] modulus = Convert.FromBase64String(publicLines[0]);
            byte[] exponent = Convert.FromBase64String(publicLines[1]);
            publicRead = true;
            string nonce, other;
            valid = Verify(modulus, exponent, expectedOwner, File.ReadAllLines(signedJob, Encoding.ASCII), out nonce);
            tamperDenied = !Verify(modulus, exponent, expectedOwner,
                                   File.ReadAllLines(forgedJob, Encoding.ASCII), out other);
            if (valid && tamperDenied && hasSid)
            {
                // Atomic create-new for same-host nonce serialization only.
                // This is NOT a proven durable Windows power-loss ledger.
                string noncePath = Path.Combine(ledger, nonce + ".nonce");
                try
                {
                    using (FileStream output = new FileStream(noncePath, FileMode.CreateNew,
                           FileAccess.Write, FileShare.None))
                    {
                        byte[] mark = Encoding.ASCII.GetBytes("J9_FAKE_CONSUMED");
                        output.Write(mark, 0, mark.Length);
                        output.Flush(true);
                        firstUse = true;
                    }
                    reason = "fresh_fake_only";
                }
                catch (IOException)
                {
                    replayDenied = File.Exists(noncePath);
                    reason = replayDenied ? "fake_replay_rejected" : "fake_ledger_error";
                }
            }
            else reason = "signature_or_identity_denied";
        }
        catch (UnauthorizedAccessException) { reason = "pinned_public_key_access_denied"; }
        catch (IOException) { reason = "fake_io_denied"; }
        catch (FormatException) { reason = "fake_public_key_invalid"; }
        using (WindowsIdentity identity = WindowsIdentity.GetCurrent())
        {
            File.WriteAllText(evidence,
                "identity=" + identity.Name + "\n" +
                "service_sid_in_actual_token=" + hasSid + "\n" +
                "pinned_public_key_read=" + publicRead + "\n" +
                "signed_fake_job_valid=" + valid + "\n" +
                "forged_signature_denied=" + tamperDenied + "\n" +
                "first_nonce_consumption=" + firstUse + "\n" +
                "replayed_nonce_denied=" + replayDenied + "\n" +
                "reason=" + reason + "\n");
        }
    }

    protected override void OnStop() { }

    private static int Main(string[] args)
    {
        if (args.Length != 7) return 2;
        ServiceBase.Run(new FakePinnedKeyWorker(args[0], args[1],
            args[2], args[3], args[4], args[5], args[6]));
        return 0;
    }
}
