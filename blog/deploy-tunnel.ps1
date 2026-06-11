# Deploy the Flask blog via Cloudflare Tunnel
# Prerequisites: pip install -r requirements.txt, cloudflared installed
# Safety: never use flask --debug behind a public tunnel

$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
$env:COOKIE_SECURE = "1"
$env:PORT = "5001"

Start-Process -NoNewWindow python -ArgumentList "app.py" -WorkingDirectory $PSScriptRoot
Write-Host "Starting Cloudflare tunnel on http://localhost:5001 ..."
cloudflared tunnel --url http://localhost:5001
