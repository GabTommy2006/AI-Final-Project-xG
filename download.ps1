param([int]$Limit = 100)
$ErrorActionPreference = 'Stop'
$auditRoot = $PSScriptRoot
$rawDirectory = Join-Path $auditRoot 'raw'
New-Item -ItemType Directory -Force -Path $rawDirectory | Out-Null
$snapshotPath = Join-Path $auditRoot 'snapshot.json'
if (Test-Path -LiteralPath $snapshotPath) {
    $snapshot = Get-Content -LiteralPath $snapshotPath -Raw | ConvertFrom-Json
} else {
    $head = Invoke-RestMethod -Uri 'https://api.github.com/repos/hudl/open-data/commits/master' -Headers @{'User-Agent'='student-xg-audit'} -TimeoutSec 30
    $snapshot = [ordered]@{repository='https://github.com/hudl/open-data';git_commit=$head.sha;retrieved_utc=[DateTime]::UtcNow.ToString('o');scope='Premier League 2015/16 competition2 season27';selected_limit=$Limit}
    $snapshot | ConvertTo-Json | Set-Content -LiteralPath $snapshotPath -Encoding utf8
}
$revision = $snapshot.git_commit
$matchesPath = Join-Path $rawDirectory 'matches_2_27.json'
if (-not (Test-Path -LiteralPath $matchesPath)) {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/hudl/open-data/$revision/data/matches/2/27.json" -OutFile $matchesPath -TimeoutSec 30
}
$matches = @(Get-Content -LiteralPath $matchesPath -Raw | ConvertFrom-Json | Sort-Object -Property match_date,match_id)
if ($Limit -gt 0) { $matches = @($matches | Select-Object -First $Limit) }
ConvertTo-Json -InputObject $matches -Depth 50 | Set-Content -LiteralPath (Join-Path $auditRoot 'selected_matches.json') -Encoding utf8
Write-Host "Downloading $($matches.Count) match files from $revision"
$results = $matches | ForEach-Object -Parallel {
    $mid=$_.match_id
    $target=Join-Path $using:rawDirectory "events_$mid.json"
    $url="https://raw.githubusercontent.com/hudl/open-data/$using:revision/data/events/$mid.json"
    $downloadError=$null
    if (-not (Test-Path -LiteralPath $target)) {
        for ($attempt=1; $attempt -le 3; $attempt++) {
            try {
                Invoke-WebRequest -Uri $url -OutFile $target -TimeoutSec 40 -ErrorAction Stop
                $downloadError=$null
                break
            } catch {
                $downloadError=$_.Exception.Message
                if ($attempt -lt 3) { Start-Sleep -Milliseconds 700 }
            }
        }
    }
    [pscustomobject]@{match_id=$mid;success=($null -eq $downloadError);error=$downloadError}
} -ThrottleLimit 6
ConvertTo-Json -InputObject @($results) -Depth 10 | Set-Content -LiteralPath (Join-Path $auditRoot 'download_status.json') -Encoding utf8
$failed=@($results | Where-Object { -not $_.success })
Write-Host "Complete: $($results.Count-$failed.Count) success; $($failed.Count) failed"
if ($failed.Count -gt 0) { throw 'Incomplete; inspect download_status.json and rerun.' }
