param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$PlanId,
    [switch]$ConfirmVerify,
    [switch]$RestartApps
)

if (-not $ConfirmVerify) {
    throw 'Verify is safety-gated. Re-run with -ConfirmVerify after reviewing the Plan.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$restartArg = @()
if ($RestartApps) {
    $restartArg = @('--restart-apps')
}
& uv run --project $repoRoot one-tone verify $PlanId --confirm @restartArg --output json
exit $LASTEXITCODE
