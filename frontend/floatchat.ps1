#floatchat.ps1
param (
    [ValidateSet("Dev","Prod")]
    [string]$Mode = "Dev"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting FloatChat in $Mode mode..."

# Load environment variables from .env
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -and ($_ -notmatch '^#')) {
            $parts = $_ -split '=', 2
            if ($parts.Length -eq 2) {
                [System.Environment]::SetEnvironmentVariable($parts[0], $parts[1], "Process")
            }
        }
    }
}

# Create logs directory
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" }

# Activate virtual environment if it exists
if (Test-Path "floatchat-frontend-env\Scripts\Activate.ps1") {
    & "floatchat-frontend-env\Scripts\Activate.ps1"
}

# Check backend connectivity
Write-Host "Checking backend connectivity..."
try {
    Invoke-WebRequest -Uri $env:BACKEND_URL/health -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "Backend is accessible at $env:BACKEND_URL"
} catch {
    if ($Mode -eq "Dev") {
        Write-Host "Backend not accessible - running in demo mode"
    } else {
        Write-Host "Backend not accessible - some features may be limited"
    }
}

# Start Streamlit server based on mode
if ($Mode -eq "Dev") {
    Write-Host "Starting development server on localhost:8501..."
    streamlit run floatchat_app.py --server.port 8501 --server.address localhost --server.headless false --server.runOnSave true
} else {
    Write-Host "Starting production server on 0.0.0.0:8501..."
    streamlit run floatchat_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true 2>&1 | Tee-Object logs\frontend.log
}
