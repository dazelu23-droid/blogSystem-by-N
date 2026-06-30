# Deploy blog-workers to Cloudflare (Windows-friendly)
# Double-click deploy.bat or run: powershell -File deploy.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Ensure-Node {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "Using system Node: $(node --version)"
        return
    }

    $nodeDir = Join-Path $env:TEMP "node-portable"
    $npx = Join-Path $nodeDir "npx.cmd"

    if (-not (Test-Path $npx)) {
        Write-Host "Node.js not found. Downloading portable Node.js (one-time)..."
        $zip = Join-Path $env:TEMP "node-win.zip"
        $extract = Join-Path $env:TEMP "node-extract"
        $url = "https://nodejs.org/dist/v22.14.0/node-v22.14.0-win-x64.zip"

        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
        if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
        Expand-Archive -Path $zip -DestinationPath $extract -Force
        if (Test-Path $nodeDir) { Remove-Item $nodeDir -Recurse -Force }
        Move-Item (Join-Path $extract "node-v22.14.0-win-x64") $nodeDir
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
        Remove-Item $extract -Recurse -Force -ErrorAction SilentlyContinue
    }

    $env:Path = "$nodeDir;$env:Path"
    Write-Host "Using portable Node: $(node --version)"
}

function Ensure-CloudflareLogin {
    $who = & npx wrangler whoami 2>&1 | Out-String
    if ($who -notmatch "not authenticated") {
        Write-Host "Cloudflare: already logged in."
        return
    }

    Write-Host ""
    Write-Host "Cloudflare login required (one-time)."
    Write-Host "A login link will appear below — open it and click Allow."
    Write-Host ""

    $loginOut = & npx wrangler login --browser=false 2>&1 | Tee-Object -Variable loginLines
    $loginText = ($loginLines | Out-String)
    if ($loginText -match "(https://dash\.cloudflare\.com/oauth2/auth\?[^\s]+)") {
        $url = $Matches[1]
        Write-Host ""
        Write-Host "Login URL:" -ForegroundColor Yellow
        Write-Host $url
        Write-Host ""
        try { Start-Process $url } catch { Write-Host "Open the URL above in your browser if it did not open automatically." }
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Login failed. Run this script again and complete the browser step."
    }

    $who = & npx wrangler whoami 2>&1 | Out-String
    if ($who -match "not authenticated") {
        Write-Error "Still not authenticated after login. Try: npx wrangler login"
    }
    Write-Host "Cloudflare login OK."
}

function Sync-WorkoutBlog {
    $src = Join-Path (Split-Path $PSScriptRoot -Parent) "workout-blog.html"
    $dst = Join-Path $PSScriptRoot "public\workout-blog.html"
    if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "Synced workout-blog.html to public/"
    }
}

Write-Host "=== Blog Workers Deploy ===" -ForegroundColor Cyan
Ensure-Node
Sync-WorkoutBlog

Write-Host "Installing dependencies..."
& npm install
if ($LASTEXITCODE -ne 0) { exit 1 }

Ensure-CloudflareLogin

Write-Host "Applying database schema (remote)..."
& npx wrangler d1 execute simple-blog-db --remote --file=schema.sql -y
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Schema apply had issues (may be OK if tables already exist)."
}

Write-Host "Deploying to Cloudflare Workers..."
& npx wrangler deploy
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "=== Deploy complete ===" -ForegroundColor Green
Write-Host 'Blog home:    https://simple-blog-by-n.dazelu.workers.dev/'
Write-Host 'Workout blog: https://simple-blog-by-n.dazelu.workers.dev/workout-blog.html'
Write-Host 'Short link:   https://simple-blog-by-n.dazelu.workers.dev/workout'
Write-Host ""
