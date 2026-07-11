param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$SeedColor,
    [Parameter(Mandatory = $true, Position = 1)]
    [string]$Targets
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
& uv run --project $repoRoot one-tone preview $SeedColor --targets $Targets --output json
exit $LASTEXITCODE
