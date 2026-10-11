# D3E30: strict and scrubbed 4663 collection contract. No log data leaves this function.
# The only real Get-WinEvent invocation exists here; synth tests replace the command
# with an in-process fake and MUST NOT read Windows Security logs or modify SACL.
function Get-D3E30Security4663Batch {
  param([Parameter(Mandatory=$true)][datetime]$StartTime)
  $raw=@()
  try{
    $raw=@(Get-WinEvent -FilterHashtable @{LogName='Security';Id=4663;StartTime=$StartTime} -MaxEvents 4000 -ErrorAction Stop)
  }catch{
    throw 'D3E30_AUDIT_QUERY_UNAVAILABLE'
  }
  if($raw.Count -eq 0){throw 'D3E30_AUDIT_ZERO_EVENTS_INCONCLUSIVE'}
  if($raw.Count -ge 4000){throw 'D3E30_AUDIT_EVENT_CAP'}
  $records=New-Object 'System.Collections.Generic.List[object]'
  foreach($item in $raw){
    # Other event IDs/providers cannot become forged write evidence.
    if($item.Id -ne 4663 -or $item.ProviderName -cne 'Microsoft-Windows-Security-Auditing'){continue}
    $fields=@{}
    try{
      $xmlString=[string]$item.ToXml()
      if([string]::IsNullOrEmpty($xmlString) -or $xmlString.Length -gt 131072){
        throw 'D3E30_XML_LENGTH_INVALID'
      }
      [xml]$doc=$xmlString
      $eventData=$doc.Event.EventData
      if($null -eq $eventData -or $null -eq $eventData.Data){
        throw 'D3E30_XML_EVENTDATA_UNAVAILABLE'
      }
      foreach($field in @($eventData.Data)){
        $key=[string]$field.GetAttribute('Name')
        if([string]::IsNullOrWhiteSpace($key)){throw 'D3E30_XML_FIELD_NAME_INVALID'}
        if($fields.ContainsKey($key)){throw 'D3E30_XML_DUPLICATE_FIELD'}
        # InnerText is an empty string even when a Data node has no #text child.
        $fields[$key]=[string]$field.InnerText
      }
    }catch{
      # The raw XML or OS error can include paths, PIDs and other personal details.
      throw 'D3E30_AUDIT_XML_INVALID'
    }
    if($fields['ObjectType'] -cne 'File'){continue}
    foreach($key in @('ObjectName','ProcessId','AccessMask')){
      if([string]::IsNullOrWhiteSpace($fields[$key])){throw 'D3E30_AUDIT_FIELDS_MISSING'}
    }
    if($fields['ProcessId'] -cnotmatch '^0[xX][0-9a-fA-F]{1,8}$'){
      throw 'D3E30_AUDIT_PID_INVALID'
    }
    if($fields['AccessMask'] -cnotmatch '^0[xX][0-9a-fA-F]{1,8}$'){
      throw 'D3E30_AUDIT_MASK_INVALID'
    }
    if($fields['ObjectName'].Length -gt 8192 -or $fields['ObjectName'].Contains([char]0)){
      throw 'D3E30_AUDIT_PATH_INVALID'
    }
    [void]$records.Add(@{
      ObjectType='File'
      ObjectName=$fields['ObjectName']
      ProcessId=$fields['ProcessId']
      AccessMask=$fields['AccessMask']
    })
  }
  # Return in memory only. Caller classifies scope & hashes identity before
  # publishing safe aggregate counts; never serialize file records to artifacts.
  return [pscustomobject]@{
    queried_event_count=[int]$raw.Count
    file_records=@($records.ToArray())
    security_4663_source='WINDOWS_EVENT_QUERY_OR_SYNTHETIC_MOCK'
  }
}
