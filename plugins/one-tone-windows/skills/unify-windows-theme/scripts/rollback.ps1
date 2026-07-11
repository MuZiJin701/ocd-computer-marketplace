param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TransactionId
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
& uv run --project $repoRoot one-tone rollback $TransactionId --output json
exit $LASTEXITCODE
