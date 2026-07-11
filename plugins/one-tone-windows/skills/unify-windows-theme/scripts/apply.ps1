param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$PlanId,
    [switch]$ConfirmApply
)

if (-not $ConfirmApply) {
    throw 'Apply is safety-gated. Re-run with -ConfirmApply after reviewing the Plan.'
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
& uv run --project $repoRoot one-tone apply $PlanId --confirm --output json
exit $LASTEXITCODE
