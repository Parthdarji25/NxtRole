# Creates the LOCAL development .env files with a random database password.
# Run it yourself from the repository root:
#   powershell -ExecutionPolicy Bypass -File scripts/new-local-env.ps1
# It never overwrites an existing file and never prints a secret.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

function New-RandomHex([int]$Bytes) {
    $buffer = New-Object byte[] $Bytes
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $generator.GetBytes($buffer)
    $generator.Dispose()
    return -join ($buffer | ForEach-Object { $_.ToString('x2') })
}

function Write-Utf8([string]$Path, [string[]]$Lines) {
    # No byte-order mark and LF endings, so every tool reads the file the same way.
    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, (($Lines -join "`n") + "`n"), $encoding)
}

$rootEnv = Join-Path $root '.env'
$apiEnv = Join-Path $root 'api/.env'
$webEnv = Join-Path $root 'web/.env.local'

if ((Test-Path $rootEnv) -or (Test-Path $apiEnv)) {
    Write-Host '.env or api/.env already exists: nothing changed. Delete both first if you want new ones.'
}
else {
    $user = 'nxtrole'
    $password = New-RandomHex 24

    Write-Utf8 $rootEnv @(
        "POSTGRES_USER=$user",
        "POSTGRES_PASSWORD=$password",
        'POSTGRES_DB=nxtrole',
        'POSTGRES_PORT=5432',
        'REDIS_PORT=6379'
    )
    Write-Utf8 $apiEnv @(
        'APP_ENV=local',
        'LOG_LEVEL=INFO',
        "DATABASE_URL=postgresql+psycopg://${user}:${password}@127.0.0.1:5432/nxtrole",
        "TEST_DATABASE_URL=postgresql+psycopg://${user}:${password}@127.0.0.1:5432/nxtrole_test",
        'REDIS_URL=redis://127.0.0.1:6379/0',
        'TEST_REDIS_URL=redis://127.0.0.1:6379/1'
    )
    Write-Host 'Created .env and api/.env'
}

if (-not (Test-Path $webEnv)) {
    Write-Utf8 $webEnv @('API_URL=http://127.0.0.1:8000')
    Write-Host 'Created web/.env.local'
}
