[CmdletBinding()]
param(
    [switch]$Down
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker CLI not found. Install and start Docker Desktop, then reopen PowerShell."
}

if ($Down) {
    docker compose down
}
else {
    docker compose up -d db redis
    docker compose ps
}
