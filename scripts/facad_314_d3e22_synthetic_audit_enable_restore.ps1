# D3E22 SYNTHETIC WINDOWS calibration on a disposable GitHub-hosted runner ONLY.
# Temporarily enables File System Success auditing for ONE subcategory, then restores it.
# Never reads vendor, patient, registry, license, or general raw event data into outputs.
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$guid='{0cce921d-69ae-11d9-bed3-505054503030}'
$root=$null
$syntheticScope=$null
$file=$null
$aclOriginal=$null
$aclApplied=$false
$aclRestored=$false
$policyOriginal=$null
$policyTouched=$false
$policyRestored=$false
$cleanupOk=$false
$workerOk=$false
$policyEnabledObserved=$false
$matchCount=0
$childCount=0
$otherCount=0
$queryOutcome='not_attempted'
$eventCount=0
$objectNameFieldCount=0
$targetSuffixMatchCount=0
$targetExactMatchCount=0
$targetWritableAccessCount=0
$liveScopedAliasCount=0
$trustedNtDevice=$null
$probeError=$false

function Get-FileAuditSuccess {
    $csvText=@(& auditpol.exe /get "/subcategory:$guid" /r 2>$null)
    if($LASTEXITCODE -ne 0 -or $csvText.Count -eq 0){throw 'AUDIT_POLICY_QUERY_UNAVAILABLE'}
    $csv=@($csvText | ConvertFrom-Csv -ErrorAction Stop)
    $matches=@($csv | Where-Object { ([string]$_.'Subcategory GUID').Trim('{} ').ToLowerInvariant() -ceq '0cce921d-69ae-11d9-bed3-505054503030' })
    if($matches.Count -ne 1){throw 'AUDIT_POLICY_GUID_NOT_FOUND'}
    $status=([string]$matches[0].'Inclusion Setting').Trim()
    if($status -match '(?i)^(success|success and failure)$'){return $true}
    if($status -match '(?i)^(no auditing|failure)$'){return $false}
    throw 'AUDIT_POLICY_STATE_UNKNOWN'
}

try {
    if($env:GITHUB_ACTIONS -cne 'true' -or $env:RUNNER_OS -cne 'Windows' -or
       $env:RUNNER_ENVIRONMENT -cne 'github-hosted' -or
       [string]::IsNullOrWhiteSpace($env:RUNNER_TEMP) -or
       [string]::IsNullOrWhiteSpace($env:GITHUB_RUN_ID)){
        throw 'GITHUB_EPHEMERAL_WINDOWS_REQUIRED'
    }
    $tempBase=[IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd('\')
    $root=Join-Path $tempBase ('FACAD-D3E22-SYNTHETIC-'+[Guid]::NewGuid().ToString('N'))
    $null=New-Item -ItemType Directory -Force -Path $root
    $syntheticScope=Join-Path $root 'AppData\Roaming\Ilexis'
    $null=New-Item -ItemType Directory -Force -Path $syntheticScope
    $file=Join-Path $syntheticScope 'synthetic.txt'
    $worker=Join-Path $root 'worker.ps1'
    [IO.File]::WriteAllText($file,'SYNTHETIC_BEFORE')
    [IO.File]::WriteAllText($worker,@'
param([Parameter(Mandatory=$true)][string]$Target)
[IO.File]::WriteAllText($Target,'SYNTHETIC_AFTER')
'@)
    . (Join-Path $PSScriptRoot 'facad_314_d3e22_event_path_map.ps1')
    $trustedNtDevice=Get-ScopedNtVolume -ScopeRoot $syntheticScope
    if([string]::IsNullOrWhiteSpace($trustedNtDevice)){throw 'TRUSTED_DRIVE_MAPPING_UNAVAILABLE'}
    $policyOriginal=Get-FileAuditSuccess
    if(-not $policyOriginal){
        $policyTouched=$true
        & auditpol.exe /set "/subcategory:$guid" /success:enable >$null 2>$null
        if($LASTEXITCODE -ne 0){throw 'AUDIT_POLICY_ENABLE_FAILED'}
    }
    $policyEnabledObserved=((Get-FileAuditSuccess) -eq $true)
    if(-not $policyEnabledObserved){throw 'AUDIT_POLICY_EFFECT_NOT_OBSERVED'}

    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    $aclOriginal=Get-Acl -LiteralPath $file -Audit -ErrorAction Stop
    $acl=Get-Acl -LiteralPath $file -Audit -ErrorAction Stop
    $rights=([Security.AccessControl.FileSystemRights]::WriteData -bor
             [Security.AccessControl.FileSystemRights]::AppendData)
    $rule=[Security.AccessControl.FileSystemAuditRule]::new(
      $identity.User,$rights,[Security.AccessControl.AuditFlags]::Success)
    $acl.AddAuditRule($rule)
    Set-Acl -LiteralPath $file -AclObject $acl -ErrorAction Stop
    $aclApplied=$true
    $readBack=Get-Acl -LiteralPath $file -Audit -ErrorAction Stop
    $matches=@($readBack.Audit | Where-Object {
        $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -ceq $identity.User.Value -and
        ([int]$_.AuditFlags -band [int][Security.AccessControl.AuditFlags]::Success) -ne 0 -and
        ([long]$_.FileSystemRights -band 0x6) -ne 0
    })
    if($matches.Count -lt 1){throw 'SYNTHETIC_FILE_SACL_MISSING'}

    $since=[DateTime]::UtcNow.AddSeconds(-2)
    $exe=(Get-Command pwsh -ErrorAction Stop).Source
    $p=Start-Process -FilePath $exe -ArgumentList ('-NoLogo -NoProfile -NonInteractive -File "'+$worker+'" -Target "'+$file+'"') -Wait -PassThru -ErrorAction Stop
    $workerOk=($p.ExitCode -eq 0 -and [IO.File]::ReadAllText($file) -ceq 'SYNTHETIC_AFTER')
    if(-not $workerOk){throw 'SYNTHETIC_CHILD_WRITE_FAILED'}
    Start-Sleep -Milliseconds 750
    $until=[DateTime]::UtcNow.AddSeconds(2)
    $records=@()
    try {
        $records=@(Get-WinEvent -FilterHashtable @{LogName='Security';Id=4663;StartTime=$since;EndTime=$until} -MaxEvents 5000 -ErrorAction Stop)
        if($records.Count -ge 5000){throw 'EVENT_LIMIT_UNTRUSTED'}
        $queryOutcome=if($records.Count){'returned'}else{'none'}
        $eventCount=$records.Count
    }catch {
        if(([string]$_.FullyQualifiedErrorId) -like 'NoMatchingEventsFound*'){
            $queryOutcome='none'
        }else{
            throw 'SECURITY_EVENT_QUERY_ERROR'
        }
    }
    foreach($ev in $records){
        try {
            if($ev.Id -ne 4663 -or $ev.ProviderName -cne 'Microsoft-Windows-Security-Auditing'){continue}
            [xml]$xml=$ev.ToXml()
            $fields=@{}
            foreach($field in $xml.Event.EventData.Data){$fields[[string]$field.Name]=[string]$field.'#text'}
            if(-not $fields.ContainsKey('ObjectName')){continue}
            $objectNameFieldCount++
            $objectName=[string]$fields.ObjectName
            $uniqueSuffix='\'+[IO.Path]::GetFileName($root)+'\AppData\Roaming\Ilexis\'+[IO.Path]::GetFileName($file)
            $suffixMatch=$objectName.EndsWith($uniqueSuffix,[StringComparison]::OrdinalIgnoreCase)
            $exactMatch=$objectName.Equals($file,[StringComparison]::OrdinalIgnoreCase)
            if($suffixMatch){$targetSuffixMatchCount++}
            if($exactMatch){$targetExactMatchCount++}
            if($suffixMatch -or $exactMatch){
                $relative=Resolve-ScopedEventRelative -ScopeRoot $syntheticScope -ObservedPath $objectName -ExpectedNtDevice $trustedNtDevice
                if($relative -ceq 'synthetic.txt'){$liveScopedAliasCount++}
            }
            if(-not ($suffixMatch -or $exactMatch) -or
               -not $fields.ContainsKey('AccessMask')){continue}
            $mask=[Convert]::ToInt64(([string]$fields.AccessMask).Replace('0x',''),16)
            if(($mask -band 0x6) -eq 0){continue}
            $targetWritableAccessCount++
            $matchCount++
            $processHex=[string]$fields.ProcessId
            if($processHex -match '^0x[0-9a-fA-F]+$' -and
                [Convert]::ToInt64($processHex.Substring(2),16) -eq [long]$p.Id){
                $childCount++
            }else{$otherCount++}
        }catch {
            $queryOutcome='invalid_event'
            $matchCount=0
            $childCount=0
            $otherCount=0
            throw 'SCOPED_EVENT_PARSE_FAILED'
        }
    }
}catch {
    # Errors are reduced to a boolean; no raw PowerShell error, paths or event content.
    $probeError=$true
}finally {
    if($aclApplied -and $null -ne $aclOriginal -and $null -ne $file -and
        (Test-Path -LiteralPath $file)){
        try {
            Set-Acl -LiteralPath $file -AclObject $aclOriginal -ErrorAction Stop
            $aclRestored=$true
        }catch{$aclRestored=$false}
    }else{$aclRestored=(-not $aclApplied)}

    if($null -ne $policyOriginal){
        if($policyTouched){
            try {
                & auditpol.exe /set "/subcategory:$guid" /success:disable >$null 2>$null
                if($LASTEXITCODE -ne 0){throw 'RESTORE_ERROR'}
                $policyRestored=((Get-FileAuditSuccess) -eq $policyOriginal)
            }catch{$policyRestored=$false}
        }else{
            try{$policyRestored=((Get-FileAuditSuccess) -eq $policyOriginal)}
            catch{$policyRestored=$false}
        }
    }
    if($null -ne $root -and (Test-Path -LiteralPath $root)){
        try{Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop}catch{}
    }
    $cleanupOk=($null -ne $root -and -not (Test-Path -LiteralPath $root))
}
Write-Host "D3E22_POLICY_EFFECTIVE=$($policyEnabledObserved.ToString().ToLowerInvariant())"
Write-Host "D3E22_CHILD_WRITE=$($workerOk.ToString().ToLowerInvariant())"
Write-Host "D3E22_4663_QUERY=$queryOutcome"
Write-Host "D3E22_4663_TOTAL_EVENT_COUNT=$eventCount"
Write-Host "D3E22_OBJECTNAME_FIELD_COUNT=$objectNameFieldCount"
Write-Host "D3E22_TARGET_SUFFIX_MATCH_COUNT=$targetSuffixMatchCount"
Write-Host "D3E22_TARGET_EXACT_MATCH_COUNT=$targetExactMatchCount"
Write-Host "D3E22_TARGET_WRITABLE_ACCESS_COUNT=$targetWritableAccessCount"
Write-Host "D3E22_TRUSTED_DEVICE_MAPPED=$([bool](-not [string]::IsNullOrWhiteSpace($trustedNtDevice)))"
Write-Host "D3E22_LIVE_SCOPED_ALIAS_MATCH_COUNT=$liveScopedAliasCount"
Write-Host "D3E22_TARGET_MATCH_COUNT=$matchCount"
Write-Host "D3E22_CHILD_PID_MATCH_COUNT=$childCount"
Write-Host "D3E22_OTHER_PID_COUNT=$otherCount"
Write-Host "D3E22_POLICY_RESTORED=$($policyRestored.ToString().ToLowerInvariant())"
Write-Host "D3E22_SACL_RESTORED=$($aclRestored.ToString().ToLowerInvariant())"
Write-Host "D3E22_PRIVATE_FILES_DELETED=$($cleanupOk.ToString().ToLowerInvariant())"
Write-Host 'D3E22_FACAD_EXECUTED=false'
Write-Host 'D3E22_RAW_SECURITY_EVENTS_EXPORTED=false'
Write-Host 'D3E22_REAL_ILEXIS_WRITER_PROVEN=false'
Write-Host 'FAC03_D3=OPEN_RED'
Write-Host 'CLINICAL_EDIT_ALLOWED=false'
if(-not $policyRestored -or -not $aclRestored -or -not $cleanupOk){
    Write-Host 'D3E22_VERDICT=BLOCKED_CLEANUP_OR_POLICY_RESTORE'
    exit 2
}
if($probeError -or -not $workerOk -or -not $policyEnabledObserved){
    Write-Host 'D3E22_VERDICT=BLOCKED_SYNTHETIC_NATIVE_PROBE_FAILED'
    exit 2
}
if($childCount -eq 0 -or $matchCount -eq 0 -or $liveScopedAliasCount -eq 0){
    Write-Host 'D3E22_VERDICT=INCONCLUSIVE_NO_SYNTHETIC_4663_PID_LINK'
    exit 3
}
Write-Host 'D3E22_VERDICT=SYNTHETIC_4663_PID_LINK_OBSERVED_NOT_FACAD'
exit 0
