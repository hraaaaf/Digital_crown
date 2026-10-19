// LOT07/07-C: strict TYPE-CHECK of isolated Command TARGET sources only.
// Uses the locked frontend compiler; deliberately does not claim a whole-app tsc pass.
const path=require('node:path');
const fs=require('node:fs');
const {createRequire}=require('node:module');
const ts=createRequire(path.resolve('frontend/package.json'))('typescript');
const pathOf=path.resolve('frontend/tsconfig.app.json');
const cfg=ts.readConfigFile(pathOf,ts.sys.readFile);
if(cfg.error)throw Error(ts.flattenDiagnosticMessageText(cfg.error.messageText,'\n'));
const parsed=ts.parseJsonConfigFileContent(cfg.config,ts.sys,path.dirname(pathOf));
if(parsed.errors.length)throw Error('Command typecheck config: '+parsed.errors.map(x=>ts.flattenDiagnosticMessageText(x.messageText,' ')).join('; '));
const target='frontend/src/features/command';
const files=['command-react-target.tsx','command-agenda.tsx','command-appointment-presentation.tsx','command-synthetic-fixtures.ts','command-synthetic-session.ts'].map(x=>path.resolve(target,x));
for(const file of files){if(!fs.existsSync(file))throw Error('Command TARGET source missing: '+file)}
const options={...parsed.options,noEmit:true,incremental:false,tsBuildInfoFile:undefined};
const program=ts.createProgram(files,options);
const diagnostics=ts.getPreEmitDiagnostics(program);
const scoped=diagnostics.filter(d=>d.file&&files.includes(path.resolve(d.file.fileName)));
const format=d=>{const where=d.file&&d.start!==undefined?d.file.getLineAndCharacterOfPosition(d.start):null;return (d.file?path.relative(process.cwd(),d.file.fileName)+':'+(where.line+1)+':'+(where.character+1)+' ':'')+'TS'+d.code+' '+ts.flattenDiagnosticMessageText(d.messageText,' ')};
const data={source:'LOT07_07C_COMMAND_TARGET_ONLY',pass:scoped.length===0,files:files.map(x=>path.relative(process.cwd(),x)),scopedErrors:scoped.map(format),otherDiagnosticsExcluded:diagnostics.length-scoped.length,wholeAppChecked:false};
const out=path.resolve('artifacts/lot07-07c-command-react');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'typecheck-target.json'),JSON.stringify(data,null,2)+'\n');
console.log('COMMAND_TARGET_TYPES '+JSON.stringify({pass:data.pass,files:data.files.length,scopedErrors:data.scopedErrors,otherDiagnosticsExcluded:data.otherDiagnosticsExcluded,wholeAppChecked:false}));
if(!data.pass)process.exitCode=1;
