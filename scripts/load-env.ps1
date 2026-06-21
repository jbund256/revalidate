param(
    [string]$Path
)

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Error "Env file not found: $Path"
    exit 1
}

Get-Content -LiteralPath $Path | ForEach-Object {
    $line = $_.Trim()

    # Skip empty lines and full-line comments
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) {
        return
    }

    # Support optional: export KEY=VALUE
    if ($line.StartsWith("export ")) {
        $line = $line.Substring(7).Trim()
    }

    # Split only on first "="
    $parts = $line -split "=", 2
    if ($parts.Count -ne 2) {
        return
    }

    $name = $parts[0].Trim()
    $value = $parts[1]

    # Remove matching surrounding quotes
    if ($value.Length -ge 2) {
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
            ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
    }

    # Set for current PowerShell process
    [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
}
