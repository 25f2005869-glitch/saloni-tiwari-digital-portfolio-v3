$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv")) { py -m venv .venv }
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not $env:ADMIN_PASSWORD) {
  $secure = Read-Host "Create your private Admin password" -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { $env:ADMIN_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N") }
$env:ADMIN_USERNAME = "saloni"
Write-Host "Starting local portfolio at http://127.0.0.1:5000" -ForegroundColor Cyan
python app.py
