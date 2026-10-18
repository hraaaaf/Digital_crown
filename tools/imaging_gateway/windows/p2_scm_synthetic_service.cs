// LOT06-P/P2-F01, disposable GitHub-hosted Windows SCM laboratory only.
// Pure synthetic bytes. No Digital Crown production code, secret, device or patient file.
using System;
using System.IO;
using System.Threading;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Diagnostics;
using System.ServiceProcess;
using System.Reflection;
using System.Text.RegularExpressions;

public sealed class P2ScmSyntheticService : ServiceBase {
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_open_v2", CharSet=CharSet.Ansi, CallingConvention=CallingConvention.Cdecl)]
    static extern int Open(string file, out IntPtr db, int flags, IntPtr vfs);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_exec", CharSet=CharSet.Ansi, CallingConvention=CallingConvention.Cdecl)]
    static extern int ExecNative(IntPtr db, string sql, IntPtr callback, IntPtr argument, out IntPtr errmsg);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_close", CallingConvention=CallingConvention.Cdecl)]
    static extern int Close(IntPtr db);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_free", CallingConvention=CallingConvention.Cdecl)]
    static extern void Free(IntPtr ptr);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_prepare_v2", CharSet=CharSet.Ansi, CallingConvention=CallingConvention.Cdecl)]
    static extern int Prepare(IntPtr db, string sql, int length, out IntPtr statement, IntPtr tail);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_step", CallingConvention=CallingConvention.Cdecl)]
    static extern int Step(IntPtr statement);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_column_text", CallingConvention=CallingConvention.Cdecl)]
    static extern IntPtr ColumnText(IntPtr statement, int index);
    [DllImport("winsqlite3.dll", EntryPoint="sqlite3_finalize", CallingConvention=CallingConvention.Cdecl)]
    static extern int FinalizeStatement(IntPtr statement);
    static volatile bool stopping;
    static Thread worker;
    // Defense in depth: never touch a DB from an arbitrary install/clinic path.
    // This LAB binary may only use the generated synthetic ProgramData layout.
    static string PrivateDir { get {
        string executable = Path.GetFullPath(Assembly.GetExecutingAssembly().Location);
        string bin = Path.GetDirectoryName(executable);
        string root = Path.GetFullPath(Path.Combine(bin, ".."));
        string rootName = Path.GetFileName(root);
        string serviceName = Path.GetFileNameWithoutExtension(executable);
        string commonData = Path.GetFullPath(Environment.GetFolderPath(
            Environment.SpecialFolder.CommonApplicationData));
        if (!String.Equals(Path.GetFileName(bin), "bin", StringComparison.OrdinalIgnoreCase)
            || !String.Equals(Path.GetDirectoryName(root), commonData, StringComparison.OrdinalIgnoreCase)
            || !Regex.IsMatch(rootName, @"^dc-p2-scm-ci-[0-9a-f]{8}$", RegexOptions.IgnoreCase)
            || !Regex.IsMatch(serviceName, @"^DCP2S[0-9a-f]{8}$", RegexOptions.IgnoreCase)
            || !String.Equals(rootName.Substring(rootName.Length - 8),
                              serviceName.Substring(serviceName.Length - 8),
                              StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("LAB_FIXTURE_LAYOUT_REQUIRED");
        return Path.Combine(root, "private");
    } }
    public P2ScmSyntheticService() { ServiceName = Path.GetFileNameWithoutExtension(Assembly.GetExecutingAssembly().Location); CanStop = true; AutoLog = false; }
    static void Sql(IntPtr db, string sql) {
        IntPtr err;
        int rc = ExecNative(db, sql, IntPtr.Zero, IntPtr.Zero, out err);
        if (rc != 0) {
            string why = err == IntPtr.Zero ? "no details" : Marshal.PtrToStringAnsi(err);
            if (err != IntPtr.Zero) Free(err);
            throw new InvalidOperationException("SQLITE_RC=" + rc.ToString() + ":" + why);
        }
    }
    // Validate values observed from SQLite; successful sqlite3_exec alone cannot
    // establish WAL mode or FULL synchronous durability on the runtime volume.
    static void ExpectScalar(IntPtr db, string sql, string expected) {
        IntPtr statement = IntPtr.Zero;
        try {
            int rc = Prepare(db, sql, -1, out statement, IntPtr.Zero);
            if (rc != 0 || statement == IntPtr.Zero)
                throw new InvalidOperationException("SQLITE_PRAGMA_PREPARE_FAILED");
            if (Step(statement) != 100)
                throw new InvalidOperationException("SQLITE_PRAGMA_ROW_MISSING");
            string actual = Marshal.PtrToStringAnsi(ColumnText(statement, 0));
            if (!String.Equals(actual, expected, StringComparison.OrdinalIgnoreCase))
                throw new InvalidOperationException("SQLITE_PRAGMA_VALUE_MISMATCH");
            if (Step(statement) != 101)
                throw new InvalidOperationException("SQLITE_PRAGMA_EXTRA_ROW");
        } finally {
            if (statement != IntPtr.Zero && FinalizeStatement(statement) != 0)
                throw new InvalidOperationException("SQLITE_PRAGMA_FINALIZE_FAILED");
        }
    }
    static void Work() {
        IntPtr db = IntPtr.Zero;
        try {
            string dir = PrivateDir, dbpath = Path.Combine(dir, "synthetic.sqlite3");
            if (Open(dbpath, out db, 0x00010006, IntPtr.Zero) != 0 || db == IntPtr.Zero)
                throw new InvalidOperationException("SQLITE_OPEN_FAILED");
            ExpectScalar(db, "PRAGMA journal_mode=WAL;", "wal");
            Sql(db, "PRAGMA synchronous=FULL;");
            ExpectScalar(db, "PRAGMA synchronous;", "2");
            Sql(db, "CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, label TEXT NOT NULL);");
            Sql(db, "BEGIN IMMEDIATE; INSERT INTO ledger(label) VALUES ('SCM_COMMITTED'); COMMIT;");
            Sql(db, "BEGIN IMMEDIATE; INSERT INTO ledger(label) VALUES ('SCM_ROLLED_BACK'); ROLLBACK;");
            Sql(db, "PRAGMA wal_checkpoint(PASSIVE);");
            var identity = WindowsIdentity.GetCurrent();
            File.WriteAllText(Path.Combine(dir,"service.ready"),
                "TOKEN_USER_SID=" + identity.User.Value + "\nSESSION_ID=" + Process.GetCurrentProcess().SessionId.ToString() +
                "\nPID=" + Process.GetCurrentProcess().Id.ToString() + "\nSQLITE_COMMIT=PASS\n");
            while (!stopping) {
                if (File.Exists(Path.Combine(dir,"trigger"))) {
                    Sql(db, "BEGIN IMMEDIATE; INSERT INTO ledger(label) VALUES ('SCM_AFTER_DENIAL'); COMMIT;");
                    Sql(db, "PRAGMA wal_checkpoint(PASSIVE);");
                    File.WriteAllText(Path.Combine(dir,"service.after"),"AFTER_DENIAL_COMMIT=PASS\n");
                    break;
                }
                Thread.Sleep(100);
            }
            while (!stopping) Thread.Sleep(150);
        }
        catch (Exception e) {
            // Type only: no environment secrets or data disclosure to CI.
            try { File.WriteAllText(Path.Combine(PrivateDir,"service.error"),e.GetType().Name); } catch {}
        }
        finally { if (db != IntPtr.Zero) Close(db); }
    }
    protected override void OnStart(string[] args) {
        stopping = false;
        worker = new Thread(Work); worker.IsBackground=true; worker.Start();
    }
    protected override void OnStop() {
        stopping=true;
        if (worker != null) worker.Join(7000);
    }
    public static void Main() { ServiceBase.Run(new P2ScmSyntheticService()); }
}
